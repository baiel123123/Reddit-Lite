import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from src.api.main import api_router
from src.config.settings import settings


def custom_generate_unique_id(route: APIRoute) -> str:
    if not isinstance(route, APIRoute):
        return route.name

    if route.tags:
        prefix = route.tags[0]
    else:
        segments = route.path.strip("/").split("/")
        prefix = segments[0] if segments[0] else "root"

    return f"{prefix}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)


origins = settings.all_cors_origins
print("CORS origins:", origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/media", StaticFiles(directory="media"), name="media")


@app.get("/")
async def root():
    return "hello"


app.include_router(api_router, prefix=settings.API_V1_STR)
