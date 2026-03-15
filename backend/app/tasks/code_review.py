import asyncio
import json
from contextlib import nullcontext
from uuid import UUID

import structlog

from app.celery_app import celery_app
from app.core.exceptions import friendly_error

logger = structlog.get_logger()


async def _run(job_id: str, code: str, language: str, user_id: str) -> None:
    from langchain_community.callbacks import get_openai_callback
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI
    from langfuse import Langfuse
    from redis.asyncio import Redis
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool

    from app.core.config import settings
    from app.core.constants import FREEZE_CREDITS
    from app.repositories.job import JobRepository
    from app.repositories.user import UserRepository
    from app.tools.code_review.prompt import CODE_REVIEW_SYSTEM_PROMPT, CODE_REVIEW_USER_TEMPLATE
    from app.tools.code_review.schemas import CodeReviewResult

    job_uuid = UUID(job_id)
    user_uuid = UUID(user_id)

    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    repo = JobRepository()
    user_repo = UserRepository()
    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    llm = ChatOpenAI(
        model="gpt-4o",
        api_key=settings.OPENAI_API_KEY,
        temperature=0,
    )
    llm_mini = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=settings.OPENAI_API_KEY,
        temperature=0,
    )

    langfuse = (
        Langfuse(
            secret_key=settings.LANGFUSE_SECRET_KEY,
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            host=settings.LANGFUSE_BASE_URL,
        )
        if settings.LANGFUSE_ENABLED
        else None
    )

    langfuse_ctx = (
        langfuse.start_as_current_observation(
            as_type="generation",
            name="code-review",
            input={"code_length": len(code), "language": language, "user_id": user_id},
        )
        if langfuse
        else nullcontext()
    )

    async with session_factory() as session:
        await repo.set_running(session, job_uuid)
        await session.commit()

    try:
        with langfuse_ctx as trace:
            try:
                await redis.publish(
                    f"job:{job_id}",
                    json.dumps({
                        "type": "status",
                        "node": "code_review",
                        "message": "Analyzing your code...",
                    }),
                )

                user_message = CODE_REVIEW_USER_TEMPLATE.format(
                    language=language or "auto-detect",
                    code=code,
                )

                total_cost_usd = 0.0
                total_input_tokens = 0
                total_output_tokens = 0

                review_span = trace.start_observation(
                    as_type="generation",
                    name="node.code_review",
                    model="gpt-4o",
                    input={
                        "system": CODE_REVIEW_SYSTEM_PROMPT,
                        "user": user_message,
                    },
                ) if trace else None

                with get_openai_callback() as cb:
                    structured_llm = llm.with_structured_output(CodeReviewResult, include_raw=True)
                    raw_result = await structured_llm.ainvoke([
                        SystemMessage(content=CODE_REVIEW_SYSTEM_PROMPT),
                        HumanMessage(content=user_message),
                    ])
                    total_cost_usd += cb.total_cost

                result: CodeReviewResult = raw_result["parsed"]
                result_dict = result.model_dump()

                if review_span:
                    usage = (raw_result["raw"].usage_metadata or {}) if raw_result.get("raw") else {}
                    inp_tok = usage.get("input_tokens", 0)
                    out_tok = usage.get("output_tokens", 0)
                    total_input_tokens += inp_tok
                    total_output_tokens += out_tok
                    review_span.update(
                        output=result_dict,
                        usage_details={"input": inp_tok, "output": out_tok},
                    )
                    review_span.end()

                title_prompt = f"Generate a concise 3-5 word title for this code review. Language: {result.language}, Score: {result.score}/10, {len(result.issues)} issues. Return ONLY the title, no quotes or extra text."

                title_span = trace.start_observation(
                    as_type="generation",
                    name="node.title_gen",
                    model="gpt-4o-mini",
                    input={"prompt": title_prompt},
                ) if trace else None

                with get_openai_callback() as cb_title:
                    title_response = await llm_mini.ainvoke([HumanMessage(content=title_prompt)])
                    total_cost_usd += cb_title.total_cost

                title = title_response.content.strip()[:100]

                if title_span:
                    usage = title_response.usage_metadata or {}
                    inp_tok = usage.get("input_tokens", 0)
                    out_tok = usage.get("output_tokens", 0)
                    total_input_tokens += inp_tok
                    total_output_tokens += out_tok
                    title_span.update(
                        output={"title": title},
                        usage_details={"input": inp_tok, "output": out_tok},
                    )
                    title_span.end()

                # Save title
                async with session_factory() as session:
                    await repo.set_title(session, job_uuid, title)
                    await session.commit()

                await redis.publish(
                    f"job:{job_id}",
                    json.dumps({
                        "type": "review",
                        "node": "code_review",
                        "data": result_dict,
                    }),
                )

                real_credits = max(1, int(total_cost_usd * settings.CREDIT_RATE * settings.CREDIT_MARKUP))

                refund = FREEZE_CREDITS - real_credits
                async with session_factory() as session:
                    if refund > 0:
                        await user_repo.refund_credits(session, user_uuid, refund)
                    elif refund < 0:
                        try:
                            await user_repo.deduct_credits(session, user_uuid, -refund)
                        except ValueError:
                            logger.warning(
                                "credits.overcharge.user_not_found",
                                user_id=user_id,
                                extra_needed=-refund,
                            )
                    await repo.set_completed(
                        session,
                        job_uuid,
                        result=result_dict,
                        credits_used=real_credits,
                    )
                    await session.commit()

                if trace:
                    trace.update(
                        output={"issues_count": len(result.issues), "score": result.score, "title": title},
                        usage_details={
                            "input": total_input_tokens,
                            "output": total_output_tokens,
                        },
                        cost_details={"total": total_cost_usd},
                    )

                await redis.publish(
                    f"job:{job_id}",
                    json.dumps({"type": "done", "job_id": job_id}),
                )
                logger.info(
                    "code_review.task.completed",
                    job_id=job_id,
                    issues=len(result.issues),
                    credits_used=real_credits,
                )

            except Exception as e:
                logger.error("code_review.task.failed", job_id=job_id, error=str(e))
                if trace:
                    trace.update(output={"error": str(e)})
                user_msg = friendly_error(e)
                async with session_factory() as session:
                    await user_repo.refund_credits(session, user_uuid, FREEZE_CREDITS)
                    await repo.set_failed(session, job_uuid, user_msg)
                    await session.commit()
                await redis.publish(
                    f"job:{job_id}",
                    json.dumps({"type": "error", "message": user_msg}),
                )
                raise

    finally:
        if langfuse:
            langfuse.flush()
        await redis.aclose()
        await engine.dispose()


@celery_app.task(name="code_review.run")
def run_code_review(job_id: str, code: str, language: str, user_id: str) -> None:
    asyncio.run(_run(job_id, code, language, user_id))
