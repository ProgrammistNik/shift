import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Конфигурационные параметры приложения, считываются из .env файла
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            ".env",
        ),
    )


settings = Settings()


def get_db_url() -> str:
    """
    Формирует URL для подключения к базе PostgreSQL через asyncpg.
    """
    
    return (
        f"postgresql+asyncpg://{settings.DB_USER}:"
        f"{settings.DB_PASSWORD}@{settings.DB_HOST}:"
        f"{settings.DB_PORT}/{settings.DB_NAME}"
    )


def get_auth_data() -> dict[str, str]:
    """
    Возвращает словарь с параметрами для JWT (секретный ключ и алгоритм).
    """

    return {
        "secret_key": settings.SECRET_KEY,
        "algorithm": settings.ALGORITHM,
    }
