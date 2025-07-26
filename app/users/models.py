from datetime import date

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import text

from app.dao.base import Base, str_uniq, int_pk, str_null_true, str_uniq_null_true


class User(Base):
    '''
    Модель пользователя.
    Поля:
    - id: первичный ключ
    - email: уникальный адрес электронной почты, обязательный
    - phone_number: уникальный номер телефона, может быть пустым
    - first_name: имя пользователя, опционально
    - last_name: фамилия пользователя, опционально
    - date_of_birth: дата рождения, опционально
    - password: хешированный пароль
    - salary: один к одному с моделью Salary, при удалении пользователя удаляется и зарплата
    '''
    
    __tablename__ = "users"
    id: Mapped[int_pk]
    email: Mapped[str_uniq]
    phone_number: Mapped[str_uniq_null_true]
    first_name: Mapped[str_null_true]
    last_name: Mapped[str_null_true]
    date_of_birth: Mapped[date] = mapped_column(nullable=True)
    password: Mapped[str]

    salary: Mapped["Salary"] = relationship(
        "Salary",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __str__(self):
        return (f"{self.__class__.__name__}(id={self.id}, "
                f"first_name={self.first_name!r},"
                f"last_name={self.last_name!r})")

    def __repr__(self):
        return str(self)
    