import pytest

from httpx import AsyncClient
from httpx import ASGITransport

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Конфигурация для тестовой SQLite БД в памяти (shared)
TEST_DATABASE_URL = "sqlite+aiosqlite:///file:test_db?mode=memory&cache=shared"

# Создаём engine и сессию для тестов
engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False, "uri": True},
)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

# Патчим модули, которые используют старые sessionmaker
import app.database as database
import app.dao.base as base_dao

database.engine = engine
database.async_session_maker = async_session_maker
base_dao.async_session_maker = async_session_maker

# Импортируем только после патчинга
from app.main import app
from app.dao.base import Base

@pytest.fixture(scope="session")
def anyio_backend():
    return 'asyncio'

@pytest.fixture(scope="function", autouse=True)
async def prepare_database():
    """
    Создаёт/очищает схему в тестовой SQLite БД shared in-memory перед каждым тестом.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture
async def client() -> AsyncClient:
    """
    HTTPX AsyncClient для тестирования FastAPI приложения.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

@pytest.fixture
async def user_token() -> str:
    """
    Регистрирует и авторизует тестового пользователя, возвращает JWT токен.
    Использует отдельный HTTPX клиент, чтобы не менять cookies основного клиента.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        register_data = {
            "email": "test@example.com",
            "password": "password123",
            "first_name": "Test",
            "last_name": "User",
            "date_of_birth": "1990-01-01"
        }
        resp = await ac.post("/auth/register/", json=register_data)
        assert resp.status_code == 201

        login_data = {"email": "test@example.com", "password": "password123"}
        resp = await ac.post("/auth/login/", json=login_data)
        assert resp.status_code == 200

        token = resp.cookies.get("users_access_token")
    return token
