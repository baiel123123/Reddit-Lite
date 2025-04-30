from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_async_session
from src.posts.dao import PostDao
from src.posts.models import Post
from src.posts.schemas import PostCreateSchema, PostFindSchema, PostUpdateSchema
from src.users.dependencies import get_current_admin_user, get_current_valid_user
from src.users.models import User
from src.utilts import hot_score

router = APIRouter(prefix="/posts", tags=["Работа с постами"])


@router.post("/create/")
async def create_post(post_data: PostCreateSchema, user: User = Depends(get_current_valid_user)):
    return await PostDao.add_forum(post_data.dict(), user)


@router.get("/get_all/", dependencies=[Depends(get_current_admin_user)])
async def get_all_posts():
    return await PostDao.find_all()


@router.get("/find/")
async def find_post(response_body: PostFindSchema = Depends()):
    return await PostDao.find_by_filter(**response_body.dict(exclude_none=True))


@router.put("/update/{post_id}", dependencies=[Depends(get_current_valid_user)])
async def update_post(post_id: int, response_body: PostUpdateSchema):
    return await PostDao.update({"id": post_id}, **response_body.dict())


@router.delete("/delete/{post_id}", dependencies=[Depends(get_current_valid_user)])
async def delete_post(post_id: int):
    return await PostDao.delete_by_id(post_id)


@router.post("/upvote/{post_id}")
async def upvote(post_id: int, is_upvote: bool, user: User = Depends(get_current_valid_user)):
    return await PostDao.up_vote(post_id, is_upvote, user)


@router.post("/delete_upvote/{post_id}")
async def delete_upvote(post_id: int, user: User = Depends(get_current_valid_user)):
    return await PostDao.remove_vote(post_id, user)


@router.get("/lenta/")
async def get_feed(
    sort_by: str = Query("hot", enum=["hot", "new", "top"]),
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(Post))
    posts = result.scalars().all()

    if sort_by == "top":
        posts.sort(key=lambda p: p.upvote, reverse=True)
    elif sort_by == "new":
        posts.sort(key=lambda p: p.created_at, reverse=True)
    else:  # hot
        posts.sort(key=lambda p: hot_score(p.upvote, p.created_at), reverse=True)

    return [{
        "id": p.id,
        "title": p.title,
        "upvotes": p.upvote,
        "created_at": p.created_at
    } for p in posts]
