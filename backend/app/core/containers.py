from dependency_injector import containers, providers
from langfuse import Langfuse
from redis.asyncio import Redis

from app.core.config import settings
from app.repositories.job import JobRepository
from app.repositories.tool import ToolRepository
from app.repositories.user import UserRepository
from app.services.job import JobService
from app.services.tool import ToolService


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=["app.api"])

    config = providers.Object(settings)

    redis_client = providers.Singleton(
        Redis.from_url,
        url=config.provided.REDIS_URL,
        decode_responses=True,
    )

    langfuse_client = providers.Singleton(
        Langfuse,
        secret_key=config.provided.LANGFUSE_SECRET_KEY,
        public_key=config.provided.LANGFUSE_PUBLIC_KEY,
        host=config.provided.LANGFUSE_BASE_URL,
        enabled=config.provided.LANGFUSE_ENABLED,
    )

    tool_repository = providers.Factory(ToolRepository)
    job_repository = providers.Factory(JobRepository)
    user_repository = providers.Factory(UserRepository)

    tool_service = providers.Factory(ToolService, repository=tool_repository)
    job_service = providers.Factory(
        JobService,
        repository=job_repository,
        user_repository=user_repository,
    )
