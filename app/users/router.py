from fastapi import APIRouter, Body, Depends, HTTPException, Path, Request, Response, status

from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError

from app.users.auth import authenticate_user, create_access_token, get_password_hash
from app.users.dao import UserDAO
from app.users.dependencies import get_current_user
from app.users.models import User
from app.users.schemas import SUserAuth, SUserCreate, SUserRead, SUserUpdate


router = APIRouter(
    tags=["Работа с пользователями"],
)


@router.post(
    "/auth/register/",
    summary="Регистрация нового пользователя",
    response_model=SUserRead,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(user_data: SUserCreate) -> SUserRead:
    '''
    Регистрирует нового пользователя.
    - Хеширует пароль.
    - Создаёт пользователя с зарплатой.
    - Обрабатывает ошибки уникальности email и телефона.
    '''

    data = user_data.model_dump(exclude={"password"})
    data["password"] = get_password_hash(user_data.password)

    try:
        user = await UserDAO.register_with_salary(data)
    except IntegrityError as e:
        msg = str(e.orig)
        # поддерживаем и Postgres, и SQLite
        if "users_email_key" in msg or "users.email" in msg:
            detail = "Такой адрес электронной почты уже используется"
        elif "users_phone_number_key" in msg or "users.phone_number" in msg:
            detail = "Такой номер телефона уже используется"
        else:
            detail = "Нарушение уникальности при создании пользователя"
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)

    return SUserRead.model_validate(user)

@router.post(
        "/auth/login/", 
        summary="Автризация пользователя")
async def auth_user(response: Response, user_data: SUserAuth):
    '''
    Аутентифицирует пользователя по email и паролю.
    - При успешной авторизации возвращаеттокен в куки.
    '''

    check = await authenticate_user(email=user_data.email, password=user_data.password)
    if check is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Неверная почта или пароль')
    access_token = create_access_token({"sub": str(check.id)})
    response.set_cookie(key="users_access_token", value=access_token, httponly=True)
    return {'access_token': access_token, 'refresh_token': None}

@router.post(
        "/logout/", 
        summary="Выход пользователя из системы", 
        status_code=status.HTTP_200_OK)
async def logout_user(request: Request, response: Response):
    '''Удаляет JWT-токен из cookies, тем самым разлогинивая пользователя.'''
    # Проверяем, есть ли кука с токеном
    token = request.cookies.get("users_access_token")

    if token is None:
        return {'message': 'Пользователь уже вышел из системы'}

    # Удаляем куку
    response.delete_cookie(key="users_access_token")
    return {'message': 'Пользователь успешно вышел из системы'}

@router.get(
        "/users/me/", 
        summary="Получить данные пользователя",
        response_model=SUserRead)
async def get_me(user_data: User = Depends(get_current_user)) -> SUserRead:
    return user_data
    
@router.patch(
    "/users/update/me",
    response_model=SUserRead,
    status_code=status.HTTP_200_OK,
    summary="Частичное обновление данных пользователя"
)
async def update_user(
    payload: SUserUpdate = Body(...),
    User = Depends(get_current_user)  # опционально
) -> SUserRead:
    # 1. Проверка, существует ли пользователь
    existing = await UserDAO.find_one_or_none_by_id(User.id)
    if not existing:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # 2. Получаем словарь обновляемых значений (только те, что не None)
    update_data = payload.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="Нет полей для обновления")

    # 3. Проверка уникальности email
    new_email = update_data.get("email")
    if new_email and new_email != existing.email:
        conflict = await UserDAO.find_one_or_none(email=new_email)
        if conflict:
            raise HTTPException(status_code=409, detail="Такой email уже используется другим пользователем")

    # 4. Проверка уникальности номера телефона
    new_phone = update_data.get("phone_number")
    if new_phone and new_phone != existing.phone_number:
        conflict = await UserDAO.find_one_or_none(phone_number=new_phone)
        if conflict:
            raise HTTPException(status_code=409, detail="Такой номер телефона уже используется другим пользователем")

    # 5. Обновление
    try:
        updated_count = await UserDAO.update(
            filter_by={"id": User.id},
            **update_data
        )
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Не удалось обновить данные пользователя")

    if not updated_count:
        raise HTTPException(status_code=404, detail="Пользователь не найден при обновлении")

    # 6. Возврат обновлённого пользователя
    updated = await UserDAO.find_one_or_none_by_id(User.id)
    return SUserRead.model_validate(updated)

@router.delete(
        "/users/delete/me", 
        status_code=204,
        summary="Удаление пользователя",
)
async def delete_user(response: Response, User = Depends(get_current_user)):
    '''
    Удаляет текущего пользователя из базы данных и очищает куки с токеном.
    Возвращает 404, если пользователь не найден.
    '''
    deleted = await UserDAO.delete_user_by_id(User.id)
    response.delete_cookie(key="users_access_token")
    if not deleted:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    