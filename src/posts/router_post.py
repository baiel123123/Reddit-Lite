from fastapi import APIRouter, Depends, Query
from sqlalchemy import Numeric, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.config.database import get_async_session
from src.posts.dao import PostDao
from src.posts.models import Post, Subscription
from src.posts.schemas import PostCreateSchema, PostFindSchema, PostUpdateSchema
from src.users.dependencies import get_current_admin_user, get_current_valid_user
from src.users.models import User

router = APIRouter(prefix="/posts", tags=["Работа с постами"])


@router.post("/create/")
async def create_post(
    post_data: PostCreateSchema, user: User = Depends(get_current_valid_user)
):
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
async def upvote(
    post_id: int, is_upvote: bool, user: User = Depends(get_current_valid_user)
):
    return await PostDao.up_vote(post_id, is_upvote, user)


@router.post("/delete_upvote/{post_id}")
async def delete_upvote(post_id: int, user: User = Depends(get_current_valid_user)):
    return await PostDao.remove_vote(post_id, user)


@router.get("/lenta/")
async def get_lenta(
    sort_by: str = Query("hot", enum=["hot", "new", "top"]),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_current_valid_user),
):
    query = select(Post).options(joinedload(Post.user), joinedload(Post.subreddit))

    if sort_by in ("top", "new"):
        sub_ids_result = await session.execute(
            select(Subscription.subreddit_id).where(Subscription.user_id == user.id)
        )
        subscribed_ids = [row[0] for row in sub_ids_result.all()]

        if not subscribed_ids:
            return []

        query = query.where(Post.subreddit_id.in_(subscribed_ids))

    if sort_by == "top":
        query = query.order_by(Post.upvote.desc())
    elif sort_by == "new":
        query = query.order_by(Post.created_at.desc())
    elif sort_by == "hot":
        hot_expr = (
            func.log(10, func.greatest(func.coalesce(Post.upvote, 0) + 1, 1)) * 0.5
            + (func.extract("epoch", Post.created_at) / cast(50000, Numeric)) * 0.5
        )
        query = query.order_by(hot_expr.desc())

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    posts = result.scalars().all()
    # TODO: return сделать в pydantic schema

    return [
        {
            "id": p.id,
            "title": p.title,
            "upvotes": p.upvote,
            "created_at": p.created_at,
            "user": {
                "id": p.user_id,
                "username": p.user.username,
            },
            "subreddit": {"id": p.subreddit_id, "name": p.subreddit.name},
        }
        for p in posts
    ]
