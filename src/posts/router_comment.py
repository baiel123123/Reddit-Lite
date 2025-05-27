from fastapi import APIRouter, Depends, Query

from src.posts.dao import CommentDao, VoteDao
from src.posts.schemas import CommentCreateSchema, CommentUpdateSchema
from src.users.dependencies import get_current_admin_user, get_current_valid_user
from src.users.models import User

router = APIRouter(prefix="/comments", tags=["Работа с комментариями"])


@router.post("/create/")
async def create_comment(
    comment_data: CommentCreateSchema, user: User = Depends(get_current_valid_user)
):
    return await CommentDao.add_forum(comment_data.dict(), user)


@router.post("/reply_to_comment/{comment_id}}")
async def reply_to_comment(
    comment_data: CommentCreateSchema, user: User = Depends(get_current_valid_user)
):
    return await CommentDao.add_forum(comment_data.dict(), user)


@router.get("/get_all/", dependencies=[Depends(get_current_admin_user)])
async def get_all_comments():
    return await CommentDao.find_all()


@router.put("/update/{comment_id}", dependencies=[Depends(get_current_valid_user)])
async def comment_update(comment_id: int, response_body: CommentUpdateSchema):
    return await CommentDao.update({"id": comment_id}, **response_body.dict())


@router.delete(
    "/get_by_id/{comment_id}", dependencies=[Depends(get_current_valid_user)]
)
async def delete_comment(comment_id: int):
    return await CommentDao.delete_by_id(comment_id)


@router.post("/upvote/{comment_id}")
async def upvote(
    comment_id: int, is_upvote: bool, user: User = Depends(get_current_valid_user)
):
    return await CommentDao.up_vote(comment_id, is_upvote, user)


@router.post("/delete_upvote/{comment_id}")
async def delete_upvote(comment_id: int, user: User = Depends(get_current_valid_user)):
    return await CommentDao.remove_vote(comment_id, user)


@router.get("/comments/by_post/{post_id}")
async def comments_with_user_votes(
    post_id: int,
    user: User = Depends(get_current_valid_user),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    comments = await CommentDao.get_comments_by_post(post_id, offset, limit)
    comment_ids = [comment.id for comment in comments]
    user_votes = await VoteDao.get_user_votes_for_comments(user.id, comment_ids)

    votes_map = {vote.comment_id: vote.is_upvote for vote in user_votes}

    response = []
    for comment in comments:
        comment_data = comment.to_dict()
        comment_data["user_vote"] = votes_map.get(comment.id, None)
        response.append(comment_data)

    return response
