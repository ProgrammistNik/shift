from datetime import datetime

from typing import Annotated
from sqlalchemy import func
from sqlalchemy import update as sqlalchemy_update
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, declared_attr, Mapped, mapped_column
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

from app.database import async_session_maker


# Аннотации
created_at = Annotated[datetime, mapped_column(server_default=func.now())]
updated_at = Annotated[datetime, mapped_column(server_default=func.now(), onupdate=func.now())]
str_uniq = Annotated[str, mapped_column(unique=True, nullable=False)]
str_uniq_null_true = Annotated[str, mapped_column(unique=True, nullable=True)]
int_pk = Annotated[int, mapped_column(primary_key=True, index=True)]
str_null_true = Annotated[str, mapped_column(nullable=True)]


# Базовый класс моделей
class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return f"{cls.__name__.lower()}s"

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]


class BaseDAO:
    model = None # Класс модели, с которой работает DAO; должен быть задан в наследниках
        

    @classmethod
    async def find_one_or_none_by_id(cls, data_id: int):
        '''Ищет запись по id, возвращает объект или None, если не найдено.'''
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(id=data_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()
    
    @classmethod
    async def find_one_or_none(cls, **filter_by):
        '''Ищет запись по произвольным фильтрам, возвращает объект или None.'''
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)
            return result.scalar_one_or_none()
            
    @classmethod
    async def update(cls, filter_by, **values):
        '''
        Обновляет поля у записи(ей), удовлетворяющих фильтру filter_by.
        Возвращает количество обновлённых строк.
        '''
        
        async with async_session_maker() as session:
            async with session.begin():
                query = (
                    sqlalchemy_update(cls.model)
                    .where(*[getattr(cls.model, k) == v for k, v in filter_by.items()])
                    .values(**values)
                    .execution_options(synchronize_session="fetch")
                )
                result = await session.execute(query)
                try:
                    await session.commit()
                except SQLAlchemyError as e:
                    await session.rollback()
                    raise e
                return result.rowcount
