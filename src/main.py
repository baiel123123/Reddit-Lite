from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.get("/as")
async def rootas():
    return {"message": "Hello, World!"}
