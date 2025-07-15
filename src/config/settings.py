from enum import Enum
from typing import Annotated, Any, List, Optional

from pydantic import AnyUrl, BeforeValidator, computed_field
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    local = "local"
    dev = "dev"
    prod = "prod"


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    ENVIRONMENT: Environment = Environment.local
    PROJECT_NAME: str = "My FastAPI App"
    API_V1_STR: str = "/api/v1"

    SENTRY_DSN: Optional[str] = None

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    @computed_field
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]

    @staticmethod
    def _parse_json_list(value: str) -> List[str]:
        import json

        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return []

    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    POSTGRES_PASSWORD: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    SMTP_SERVER: str
    SMTP_PORT: int
    EMAIL_FROM: str
    EMAIL_PASSWORD: str
    REDIS_URL: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()


def get_db_url():
    return (
        f"postgresql+asyncpg://{settings.DB_USER}:{settings.POSTGRES_PASSWORD}@"
        f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )


def get_auth_data():
    return {
        "secret_key": settings.SECRET_KEY,
        "algorithm": settings.ALGORITHM,
        "access_token_expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    }


def get_email_settings():
    return {
        "smtp_server": settings.SMTP_SERVER,
        "smtp_port": settings.SMTP_PORT,
        "email_from": settings.EMAIL_FROM,
        "email_password": settings.EMAIL_PASSWORD,
    }


def get_redis_url():
    return settings.REDIS_URL
