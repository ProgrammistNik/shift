from fastapi import APIRouter, Body, Depends, HTTPException, Path, status

from app.salary.dao import SalaryDAO
from app.salary.schemas import SSalary
from app.users.dependencies import get_current_user
from app.users.models import User


router = APIRouter(
    prefix='/salary',
    tags=["Работа с зарплатой"]
)

@router.get(
    '/me/',
    summary="Получить данные зарплаты пользователя",
    response_model=SSalary,
    status_code=status.HTTP_200_OK,
)
async def get_salary_by_user(User = Depends(get_current_user)) -> SSalary:
    salary = await SalaryDAO.find_salary_by_user_id(User.id)
    if not salary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Данные о зарплате пользователя с ID {User.id} не найдены",
        )
    return SSalary.model_validate(salary)  # важно: нужен from_attributes=True в SSalary
