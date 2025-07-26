from datetime import date, timedelta

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.dao.base import Base, int_pk
from app.users.models import User


def default_next_raise_date():
    '''
    Функция по умолчанию для поля next_raise_date:
    возвращает дату через 180 дней от текущей.
    '''
    return date.today() + timedelta(days=180)


class Salary(Base):
    '''
    Модель зарплаты, связанная с пользователем.

    Атрибуты:
    - id: первичный ключ записи зарплаты
    - amount: сумма зарплаты, по умолчанию 80_000
    - next_raise_date: дата следующего повышения зарплаты (опционально, по умолчанию через 180 дней)
    - user_id: внешний ключ на таблицу пользователей (users.id), каскадное удаление
    - user: связь ORM с моделью пользователя (обратная связь)
    '''
        
    __tablename__ = "salary"
    id: Mapped[int_pk]
    amount: Mapped[int] = mapped_column(default=80000)
    next_raise_date: Mapped[date] = mapped_column(
            default=default_next_raise_date,
            nullable=True
    )

    user_id: Mapped[int] = mapped_column(
    ForeignKey("users.id", ondelete="CASCADE"),
    nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="salary")

    def __str__(self):
        return (f"{self.__class__.__name__}(id={self.id}), "
                f"salary_id={self.id!r}")

    def __repr__(self):
        return str(self)
    