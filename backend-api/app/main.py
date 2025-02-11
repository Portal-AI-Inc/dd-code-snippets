import os
import sys
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from alembic import command, config
from sqlalchemy.ext.asyncio import create_async_engine

from app.graphql.errors import UnauthorizedError
from app.utils import logging_config
from app.utils.context_management import set_loop
from app.utils.middleware import add_request_id, add_user_id, log_request
from app.utils.sentry_scrub import scrub_email

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import sentry_sdk
from sentry_sdk.scrubber import EventScrubber
from sentry_sdk.integrations.strawberry import StrawberryIntegration
from app.config import settings, Environment
from app.database import sessionmanager
from app.tasks import handle_hanging_integration_connections_task
from app.routers.auth import router as auth_router
from app.routers.health_check import router as health_check_router
from app.routers.integrations import router as integrations_router
from app.routers.oauth import router as oauth_router
from app.routers.stripe import router as stripe_router
from app.routers.tiktok import router as tiktok_router
from app.routers.graphql import router as graphql_router
from app.routers.gupshup import router as gupshup_router
from app.routers.file import router as file_router


if settings.SENTRY_DSN and settings.ENV != Environment.LOCAL:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENV.value,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for tracing.
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
        send_default_pii=False,
        ignore_errors=[UnauthorizedError],
        integrations=[
            StrawberryIntegration(async_execution=True),
        ],
        event_scrubber=EventScrubber(),
        before_send=scrub_email,
    )


def run_upgrade(connection, cfg):
    cfg.attributes["connection"] = connection
    command.upgrade(cfg, "heads")


async def run_async_upgrade():
    alembic_cfg = config.Config("alembic.ini")
    async_engine = create_async_engine(settings.DATABASE_URL)

    async with async_engine.begin() as conn:
        await conn.run_sync(run_upgrade, alembic_cfg)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Function that handles startup and shutdown events.
    To understand more, read https://fastapi.tiangolo.com/advanced/events/
    """
    await run_async_upgrade()
    logging_config.setup_loguru()
    loop = asyncio.get_running_loop()
    set_loop(loop)
    await handle_hanging_integration_connections_task()

    yield

    if sessionmanager._engine is not None:
        # Close the DB connection
        await sessionmanager.close()


app = FastAPI(lifespan=lifespan, title=settings.PROJECT_NAME, docs_url="/api-docs")


app.middleware("http")(add_request_id)
app.middleware("http")(add_user_id)
app.middleware("http")(log_request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: allow web app and also urls like https://*.myshopify.com
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    health_check_router,
    prefix="/health",
    tags=["status"],
)
app.include_router(
    oauth_router,
    prefix="/token",
    tags=["auth"],
)
app.include_router(
    graphql_router,
    prefix="/graphql",
    tags=["graphql"],
)
app.include_router(
    integrations_router,
    prefix="/integrations",
    tags=["integrations"],
)
app.include_router(
    auth_router,
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    stripe_router,
    prefix="/stripe",
    tags=["stripe"],
)
app.include_router(
    tiktok_router,
    prefix="/tiktok",
    tags=["tiktok"],
)
app.include_router(
    gupshup_router,
    prefix="/gupshup",
    tags=["gupshup"],
)
app.include_router(
    file_router,
    prefix="/file",
    tags=["file"],
)
