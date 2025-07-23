from fastapi import FastAPI
from routers import pessoa, terreno, contrucao, obra

app = FastAPI()

routers = [pessoa.router, terreno.router, contrucao.router, obra.router]

for router in routers:
    app.include_router(router)
