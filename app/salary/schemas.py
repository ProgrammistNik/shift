from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing_extensions import Annotated
from typing import Optional


class SSalary(BaseModel):
    '''
    Pydantic-модель для описания данных зарплаты пользователя.

    Поля:
    - id: уникальный идентификатор зарплаты (целое число > 0)
    - amount: сумма зарплаты (целое число >= 0)
    - next_raise_date: дата следующего повышения зарплаты (опционально, должна быть в будущем)
    '''

    model_config = ConfigDict(from_attributes=True)

    id: Annotated[
        int, 
        Field(
            gt=0,
            alias="id",
            description="Уникальный идентификатор зарплаты, больше 0"
        )
    ]

    amount: Annotated[
        int, 
        Field(
            ge=0,
            default=..., 
            description="Зарплата пользователя, больше или равная 0"
        )
    ]
    
    next_raise_date: Optional[date] = Field(
        default=None,
        description="Дата следующего повышения зарплаты"
    )

    
    @field_validator("next_raise_date")
    @classmethod
    def validate_next_raise(cls, value: date):
        '''
        Валидатор для поля next_raise_date:
        - допускает None
        - если указана дата, проверяет, что она в будущем (больше текущей даты)
        '''
        
        if value is None:
            return value
        if value <= datetime.now().date():
            raise ValueError("Дата следующего повышения должна быть в будущем")
        return value
