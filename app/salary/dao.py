from sqlalchemy.future import select

from app.dao.base import BaseDAO
from app.database import async_session_maker
from app.salary.models import Salary


class SalaryDAO(BaseDAO):
    model = Salary
    
    @classmethod
    async def find_salary_by_user_id(cls, user_id: int):
        '''
        Асинхронно ищет запись зарплаты по ID пользователя.
        
        Возвращает объект Salary или None, если запись не найдена.
        '''
        
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(user_id=user_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()
        