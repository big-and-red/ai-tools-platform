import asyncio
import json
from contextlib import nullcontext
from uuid import UUID

import structlog

from app.celery_app import celery_app
from app.core.exceptions import friendly_error

logger = structlog.get_logger()


async def _run(job_id: str, query: str, user_id: str) -> None:
    from langchain_community.callbacks import get_openai_callback
    from langchain_openai import ChatOpenAI
    from langfuse import Langfuse
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from redis.asyncio import Redis
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool

    from app.agents.research.graph import build_research_graph
    from app.core.config import settings
    from app.core.constants import FREEZE_CREDITS
    from app.repositories.job import JobRepository
    from app.repositories.user import UserRepository

    job_uuid = UUID(job_id)
    user_uuid = UUID(user_id)

    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    repo = JobRepository()
    user_repo = UserRepository()
    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
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
            name="research-agent",
            input={"query": query, "user_id": user_id},
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
                async with AsyncPostgresSaver.from_conn_string(
                    settings.PG_DSN
                ) as checkpointer:
                    await checkpointer.setup()
                    graph = build_research_graph().compile(checkpointer=checkpointer)

                    initial_state = {
                        "query": query,
                        "job_id": job_id,
                        "questions": [],
                        "search_results": [],
                        "retry_count": 0,
                        "is_sufficient": True,
                        "report": None,
                        "formatted_output": "",
                    }
                    run_config = {
                        "configurable": {
                            "thread_id": job_id,
                            "llm": llm,
                            "redis": redis,
                            "tavily_api_key": settings.TAVILY_API_KEY,
                            "langfuse_trace": trace,
                        },
                        "callbacks": [],
                    }

                    with get_openai_callback() as cb:
                        final_state = await graph.ainvoke(initial_state, config=run_config)

                llm_cost_usd = cb.total_cost
                tavily_calls = len(final_state.get("questions", []))
                tavily_cost_usd = tavily_calls * settings.TAVILY_ADVANCED_COST_USD
                total_cost_usd = llm_cost_usd + tavily_cost_usd
                real_credits = max(1, int(total_cost_usd * settings.CREDIT_RATE * settings.CREDIT_MARKUP))

                refund = FREEZE_CREDITS - real_credits
                async with session_factory() as session:
                    if refund > 0:
                        await user_repo.refund_credits(session, user_uuid, refund)
                    elif refund < 0:
                        # Cost exceeded freeze — deduct extra (balance may go negative)
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
                        result={"formatted_output": final_state.get("formatted_output", "")},
                        credits_used=real_credits,
                    )
                    await session.commit()

                if trace:
                    trace.update(
                        output={"report_length": len(final_state.get("formatted_output", ""))},
                        usage_details={
                            "input": cb.prompt_tokens,
                            "output": cb.completion_tokens,
                            "total": cb.total_tokens,
                        },
                        cost_details={
                            "total": llm_cost_usd + tavily_cost_usd,
                        },
                        metadata={
                            "tavily_calls": tavily_calls,
                            "credits_used": real_credits,
                        },
                    )
                # No trace.end() — context manager handles it on with-block exit

                await redis.publish(
                    f"job:{job_id}",
                    json.dumps({"type": "done", "job_id": job_id}),
                )
                logger.info(
                    "research.task.completed",
                    job_id=job_id,
                    credits_used=real_credits,
                    llm_cost_usd=llm_cost_usd,
                    tavily_calls=tavily_calls,
                )

            except Exception as e:
                logger.error("research.task.failed", job_id=job_id, error=str(e))
                if trace:
                    trace.update(output={"error": str(e)})
                user_msg = friendly_error(e)
                # trace auto-ends when with-block exits after exception
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


@celery_app.task(name="research.run")
def run_research_agent(job_id: str, query: str, user_id: str) -> None:
    asyncio.run(_run(job_id, query, user_id))
