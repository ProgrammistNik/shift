import pytest

from httpx import AsyncClient

from app.database import async_session_maker
from app.salary.dao import SalaryDAO
from app.users.dao import UserDAO


class TestSalaryEndpoints:
    async def test_get_salary_success(self, client: AsyncClient, user_token: str):
        '''
        Проверяет успешное получение данных зарплаты авторизованного пользователя.
        - Отправляет запрос с валидным токеном в cookie.
        - Проверяет, что статус 200.
        - Проверяет наличие полей amount и next_raise_date в ответе.
        '''
        resp = await client.get(
            "/salary/me/",
            headers={"Cookie": f"users_access_token={user_token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "amount" in data and "next_raise_date" in data

    async def test_get_salary_not_found(self, client: AsyncClient, user_token: str):
        '''
        Проверяет поведение при отсутствии записи зарплаты у пользователя.
        - Удаляет зарплату напрямую через сессию.
        - Отправляет запрос с валидным токеном.
        - Проверяет, что возвращается 404 и соответствующее сообщение.
        '''

        user = await UserDAO.find_one_or_none(email="test@example.com")
        async with async_session_maker() as session:
            salary = await SalaryDAO.find_salary_by_user_id(user.id)
            await session.delete(salary)
            await session.commit()

        resp = await client.get(
            "/salary/me/",
            headers={"Cookie": f"users_access_token={user_token}"}
        )
        assert resp.status_code == 404
        assert "не найдены" in resp.json()["detail"]

    @pytest.mark.parametrize("token_header", [
        {},  # без токена
        {"Cookie": "users_access_token=badtoken"}  # некорректный токен
    ])
    async def test_get_salary_unauthorized(self, client: AsyncClient, token_header):
        '''
        Проверяет отказ в доступе при отсутствии или некорректном токене.
        - Использует параметризацию для проверки нескольких вариантов.
        - Проверяет, что возвращается 401.
        '''
                
        resp = await client.get("/salary/me/", headers=token_header)
        assert resp.status_code == 401
