from fastapi import FastAPI

from src.users.router import router as user_routers

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello, World!"}

app.include_router(user_routers)
