import pytest

from httpx import AsyncClient


class TestUserEndpoints:

    async def test_register_success(self, client: AsyncClient):
        '''
        Проверяет успешную регистрацию нового пользователя с валидными данными.
        Проверяется статус 201 и корректность возвращённых данных.
        '''
        resp = await client.post(
            "/auth/register/",
            json={
                "email": "new@example.com",
                "password": "password123",
                "first_name": "Пётр",
                "last_name": "Петров",
                "date_of_birth": "1995-05-05"
            }
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] > 0
        assert data["email"] == "new@example.com"

    @pytest.mark.parametrize("payload, field", [
        ({"email": "bademail", "password": "password123"}, "email"),
        ({"email": "ok@example.com", "password": "short"}, "password"),
    ])
    async def test_register_validation_error(self, client: AsyncClient, payload, field):
        '''
        Проверяет валидацию данных при регистрации.
        Использует параметризацию для проверки разных полей:
        - неправильный email
        - слишком короткий пароль
        Проверяет, что возвращается 422 с ошибкой на нужном поле.
        '''

        full = {
            "first_name": "А",
            "last_name": "Б",
            "date_of_birth": "2005-01-01",  # <18 лет
            **payload
        }
        resp = await client.post("/auth/register/", json=full)
        assert resp.status_code == 422
        errors = resp.json()["detail"]
        assert any(err["loc"][-1] == field for err in errors)

    async def test_register_conflict(self, client: AsyncClient):
        '''Проверяет ошибку при попытке регистрации с уже существующим email.'''
        await client.post(
            "/auth/register/",
            json={
                "email": "dup@example.com",
                "password": "password123",
                "first_name": "Ирина",
                "last_name": "Иванова",
                "date_of_birth": "1992-02-02"
            }
        )
        resp = await client.post(
            "/auth/register/",
            json={
                "email": "dup@example.com",
                "password": "password456",
                "first_name": "Игорь",
                "last_name": "Игорев",
                "date_of_birth": "1990-03-03"
            }
        )
        assert resp.status_code == 409
        assert "электронной почты" in resp.json()["detail"]

    async def test_login_wrong_credentials(self, client: AsyncClient):
        '''Проверяет отказ при неверных учетных данных на входе.'''
        resp = await client.post(
            "/auth/login/",
            json={"email": "noone@example.com", "password": "whatever123"}
        )
        assert resp.status_code == 401

    async def test_get_me_success_and_unauthorized(self, client: AsyncClient, user_token: str):
        '''Проверяет получение данных авторизованного пользователя и отказ без токена.'''
        resp = await client.get(
            "/users/me/",
            headers={"Cookie": f"users_access_token={user_token}"}
        )
        assert resp.status_code == 200
        assert "email" in resp.json()

        resp2 = await client.get("/users/me/")
        assert resp2.status_code == 401

    async def test_update_no_fields(self, client: AsyncClient, user_token: str):
        '''Проверяет ошибку при попытке обновления без указания полей.'''
        resp = await client.patch(
            "/users/update/me",
            headers={"Cookie": f"users_access_token={user_token}"},
            json={}
        )
        assert resp.status_code == 400
        assert "Нет полей для обновления" in resp.json()["detail"]

    async def test_update_conflict_email(self, client: AsyncClient, user_token: str):
        '''Проверяет ошибку при попытке обновить email на уже используемый другим пользователем.'''
        await client.post(
            "/auth/register/",
            json={
                "email": "other@example.com",
                "password": "password123",
                "first_name": "AAA",
                "last_name": "BBB",
                "date_of_birth": "1990-01-01"
            }
        )
        resp = await client.patch(
            "/users/update/me",
            headers={"Cookie": f"users_access_token={user_token}"},
            json={"email": "other@example.com"}
        )
        assert resp.status_code == 409
        assert "email уже используется" in resp.json()["detail"]

    async def test_delete_and_access(self, client: AsyncClient, user_token: str):
        '''Проверяет удаление текущего пользователя и последующий отказ в доступе.'''
        resp = await client.delete(
            "/users/delete/me",
            headers={"Cookie": f"users_access_token={user_token}"}
        )
        assert resp.status_code == 204

        resp2 = await client.get(
            "/users/me/",
            headers={"Cookie": f"users_access_token={user_token}"}
        )
        assert resp2.status_code in (401, 404)
