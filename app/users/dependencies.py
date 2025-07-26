from fastapi import Request, HTTPException, status, Depends
from jose import jwt, JWTError
from datetime import datetime, timezone

from app.config import settings
from app.users.dao import UserDAO


SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
COOKIE_NAME = "users_access_token"


def get_token(request: Request):
    '''
    Извлекает JWT токен из cookies запроса
    Если токен отсутствует — HTTP 401.
    '''
    
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token not found')
    return token

  
async def get_current_user(token: str = Depends(get_token)):
    '''
    Извлекает и проверяет текущего пользователя по JWT токену.

    проверка:
    - валидность токена
    - срок действия токена (exp)
    - наличие user_id в поле "sub" токена
    - существование пользователя в базе данных

    Возвращает объект пользователя или - HTTP 401.
    '''

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Токен не валидный!')

    expire = payload.get('exp')
    expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)
    if (not expire) or (expire_time < datetime.now(timezone.utc)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Токен истек')

    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Не найден ID пользователя')

    user = await UserDAO.find_one_or_none_by_id(int(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')

    return user
