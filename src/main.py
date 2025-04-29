from fastapi import FastAPI

from src.posts.router_comment import router as comment_routers
from src.posts.router_post import router as post_routers
from src.posts.router_subreddit import router as subreddit_routers
from src.tasks.hi import welcome
from src.users.router import router as user_routers

app = FastAPI()


@app.get("/")
async def root():
    welcome.apply_async()
    return {"message": "Hello, World!"}

app.include_router(user_routers)
app.include_router(subreddit_routers)
app.include_router(comment_routers)
app.include_router(post_routers)
