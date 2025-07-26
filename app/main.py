from fastapi import FastAPI

from app.users.router import router as router_users
from app.salary.router import router as router_salary


app = FastAPI()

@app.get("/")
def home_page():
    return {"message": "Salaty-service!"}

# Подключаем маршруты для пользователей и с зарплатами
app.include_router(router_users)
app.include_router(router_salary)
