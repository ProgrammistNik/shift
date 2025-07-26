from datetime import date, datetime
import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from typing_extensions import Annotated
from typing import Optional


class SUserBase(BaseModel):
    '''
    Базовая схема пользователя с необязательными полями.
    Содержит общие для всех операций поля и валидации.
    '''

    email: Optional[EmailStr] = Field(
        default=None,
        description="Электронная почта пользователя"
    )

    phone_number: Optional[str] = Field(
        default=None,
        description="Номер телефона в международном формате, начинающийся с '+'"
    )

    first_name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=50,
        description="Имя пользователя от 2 до 50 символов"
    )

    last_name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=50,
        description="Фамилия пользователя от 2 до 50 символов"
    )

    date_of_birth: Optional[date] = Field(
        default=None,
        description="Дата рождения пользователя в формате ГГГГ-ММ-ДД"
    )

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: Optional[str]) -> Optional[str]:
        '''
        Валидирует номер телефона:
        - либо None,
        - либо строка, начинающаяся с '+' и содержащая от 1 до 15 цифр.
        '''
        if value is None:
            return value
        if not re.match(r'^\+\d{1,15}$', value):
            raise ValueError("Номер телефона должен начинаться с '+' и содержать от 1 до 15 цифр")
        return value

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value: Optional[date]) -> Optional[date]:
        '''
        Валидирует дату рождения:
        - либо None,
        - либо проверяет, что возраст пользователя не менее 18 лет.
        '''
        if value is None:
            return value
        today = datetime.now().date()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 18:
            raise ValueError("Возраст должен быть не менее 18 лет")
        return value
    

class SUserCreate(SUserBase):
    email: EmailStr  # переопределяем как required
    password: Annotated[
        str,
        Field(
            min_length=8,
            max_length=24,
            repr=False,
            description="Пароль пользователя от 8 до 24 символов"
        )
    ]

    model_config: ConfigDict = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "phone_number": "+79999999999",
                "first_name": "Иван",
                "last_name": "Иванов",
                "date_of_birth": "1990-05-15",
                "password": "strongP@ssw0rd"
            }
        }
    )


# Схема для ответа (выходная). Тут уже есть id.
class SUserRead(SUserBase):
    '''
    Схема для чтения данных пользователя (выходная).
    Добавляет обязательный id.
    '''

    id: int

    model_config = ConfigDict(from_attributes=True)


class SUserUpdate(SUserBase):
    '''
    Схема для частичного обновления пользователя.
    Все поля — необязательные, для частичного обновления.
    '''
    pass

class SUserAuth(BaseModel):
    '''
    Схема для авторизации пользователя.
    Требует email и пароль с длиной от 8 до 24 символов.
    '''
    email: EmailStr  # переопределяем как required
    password: Annotated[
        str,
        Field(
            min_length=8,
            max_length=24,
            exclude=True,
            description="Пароль пользователя от 8 до 24 символов"
        )
    ]
