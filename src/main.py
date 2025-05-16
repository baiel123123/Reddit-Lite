from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.posts.router_comment import router as comment_routers
from src.posts.router_post import router as post_routers
from src.posts.router_subreddit import router as subreddit_routers
from src.users.router import router as user_routers

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return "hello"


app.include_router(user_routers)
app.include_router(subreddit_routers)
app.include_router(comment_routers)
app.include_router(post_routers)
