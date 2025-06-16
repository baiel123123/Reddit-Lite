import os
import shutil
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import Numeric, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config.database import get_async_session
from src.posts.dao import PostDao, SubredditDao, VoteDao
from src.posts.models import Post, Subscription
from src.posts.schemas import (
    PostCreateForm,
    PostFindSchema,
    PostUpdateSchema,
)
from src.users.dependencies import (
    get_current_admin_user,
    get_current_user,
    get_current_valid_user,
)
from src.users.models import User

router = APIRouter(prefix="/posts", tags=["Работа с постами"])


@router.post("/create/")
async def create_post(
    form: PostCreateForm = Depends(),
    image: UploadFile = File(None),
    user: User = Depends(get_current_valid_user),
):
    image_path = None
    if image:
        ext = os.path.splitext(image.filename)[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join("media", filename)
        os.makedirs("media", exist_ok=True)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        image_path = file_path

    post_data = {
        "title": form.title,
        "content": form.content,
        "subreddit_id": form.subreddit_id,
        "image_path": image_path,
    }
    return await PostDao.add_forum(post_data, user)


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
async def upvote(post_id: int, is_upvote: bool, user: User = Depends(get_current_user)):
    return await PostDao.up_vote(post_id, is_upvote, user)


@router.post("/delete_upvote/{post_id}")
async def delete_upvote(post_id: int, user: User = Depends(get_current_user)):
    return await PostDao.remove_vote(post_id, user)


@router.get("/lenta/")
async def get_lenta(
    sort_by: str = Query("hot", enum=["hot", "new", "top"]),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_current_user),
):
    query = select(Post).options(selectinload(Post.user), selectinload(Post.subreddit))

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

    return [
        {
            "id": p.id,
            "title": p.title,
            "content": p.content,
            "upvote": p.upvote,
            "created_at": p.created_at,
            "user": {
                "id": p.user_id,
                "username": p.user.username if p.user else "Неизвестный",
            },
            "subreddit": {"id": p.subreddit_id, "name": p.subreddit.name},
            "image_path": p.image_path,
            "comments_count": p.comments_count,
        }
        for p in posts
    ]


@router.get("/my_posts")
async def get_my_posts(user: User = Depends(get_current_user)):
    posts = await PostDao.find_my_posts(user_id=user.id)
    if not posts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    return posts


@router.get("/{post_id}")
async def get_post_by_id(post_id: int):
    post = await PostDao.find_one_or_none(id=post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    subreddit = await SubredditDao.find_one_or_none_by_id(post.subreddit_id)
    post_data = post.to_dict()
    post_data["subreddit_name"] = subreddit.name if subreddit else "Неизвестно"
    return post_data


@router.get("/user_posts/")
async def get_user_posts(user_id: int):
    posts = await PostDao.find_my_posts(user_id=user_id)
    if not posts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    return posts


@router.get("/votes/by-user")
async def get_post_votes_by_user(
    ids: str = Query(..., description="Comma-separated list of IDs"),
    current_user: User = Depends(get_current_user),
):
    if not ids:
        return []
    id_list = [int(i) for i in ids.split(",")]
    votes = await VoteDao.get_post_votes_by_user(current_user.id, id_list)

    return {vote["target_id"]: vote["is_upvote"] for vote in votes}


@router.get("/by-subreddit/{subreddit_id}")
async def get_posts_by_subreddit(
    subreddit_id: int, limit: int = Query(20, ge=1, le=100), offset: int = Query(0)
):
    posts = await PostDao.get_posts_by_subreddit_id(subreddit_id, limit, offset)
    if not posts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    return posts
