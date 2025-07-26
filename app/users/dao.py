from datetime import date, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy import delete
from sqlalchemy.future import select

from app.database import async_session_maker
from app.dao.base import BaseDAO
from app.salary.models import Salary
from app.users.models import User


class UserDAO(BaseDAO):
    model = User

    @classmethod
    async def register_with_salary(cls, user_data: dict) -> User:
        '''Регистрирует нового пользователя и одновременно создает связанную запись зарплаты'''
        async with async_session_maker() as session:
            try:
                async with session.begin():
                    # 1. Создаем пользователя
                    user = User(**user_data)
                    session.add(user)
                    await session.flush()  # получаем user.id

                    # 2. Создаем зарплату
                    salary = Salary(user_id=user.id)
                    session.add(salary)

                return user

            except IntegrityError as e:
                raise e

    @classmethod
    async def delete_user_by_id(cls, user_id: int):
        '''Удаляет пользователя по ID, если он существует.'''
        async with async_session_maker() as session:
            result = await session.execute(select(cls.model).filter_by(id=user_id))
            user = result.scalar_one_or_none()
            if not user:
                return False
            await session.delete(user)
            await session.commit()
            return True
