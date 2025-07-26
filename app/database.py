from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.config import get_db_url


DATABASE_URL = get_db_url()
# Создаем асинхронный движок SQLAlchemy для подключения к базе данных
engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
)
