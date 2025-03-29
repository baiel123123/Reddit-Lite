from fastapi import APIRouter, Depends

from src.posts.dao import SubredditDao, PostDao, CommentDao
from src.posts.schemas import PostCreateSchema, SubRedditCreateSchema, CommentCreateSchema, SubRedditFindSchema, \
    SubRedditUpdateSchema, PostFindSchema, PostUpdateSchema

from src.users.dependencies import get_current_valid_user, get_current_admin_user, get_current_super_admin_user
from src.users.models import User


router = APIRouter(prefix="/subreddit", tags=["Работа с сабреддитами"])


@router.post('/create')
async def create_subreddit(subreddit_data: SubRedditCreateSchema, user: User = Depends(get_current_valid_user)):
    return await SubredditDao.add_forum(subreddit_data.dict(), user)


@router.get('/get_all/', dependencies=[Depends(get_current_admin_user)])
async def get_all_subreddit():
    return await SubredditDao.find_all()


@router.get("/find/")
async def find_subreddit(response_body: SubRedditFindSchema = Depends()):
    return await SubredditDao.find_by_filter(response_body.dict(exclude_none=True))


@router.put("/update/{subreddit_id}", dependencies=[Depends(get_current_valid_user)])
async def update_subreddit(subreddit_id: int, response_body: SubRedditUpdateSchema):
    return await SubredditDao.update({"id": subreddit_id}, **response_body.dict())


@router.delete("/delete/{subreddit_id}", dependencies=[Depends(get_current_super_admin_user)])
async def delete_subreddit(subreddit_id: int):
    return await SubredditDao.delete_by_id(subreddit_id)
