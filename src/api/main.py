from fastapi import APIRouter

from src.posts import router_comment, router_post, router_subreddit
from src.users import router

api_router = APIRouter()

api_router.include_router(router_comment.router)
api_router.include_router(router_post.router)
api_router.include_router(router_subreddit.router)
api_router.include_router(router.router)
