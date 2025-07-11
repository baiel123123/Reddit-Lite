from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from src.posts.router_comment import router as comment_routers
from src.posts.router_post import router as post_routers
from src.posts.router_subreddit import router as subreddit_routers
from src.users.router import router as user_routers

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://193.46.198.101"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/media", StaticFiles(directory="media"), name="media")


@app.get("/")
async def root():
    return "hello"


app.include_router(user_routers)
app.include_router(subreddit_routers)
app.include_router(comment_routers)
app.include_router(post_routers)
