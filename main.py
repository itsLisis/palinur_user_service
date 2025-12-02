from fastapi import FastAPI
from db import Base, engine

from routers import users_router


app = FastAPI(title="User Service")

Base.metadata.create_all(bind=engine)

app.include_router(users_router.router)