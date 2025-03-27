from fastapi import APIRouter, Depends

from src.posts.dao import SubredditDao, PostDao, CommentDao
from src.posts.schemas import PostCreateSchema, SubRedditCreateSchema, CommentCreateSchema, SubRedditFindSchema, \
    SubRedditUpdateSchema, PostFindSchema, PostUpdateSchema

from src.users.dependencies import get_current_valid_user, get_current_admin_user, get_current_super_admin_user
from src.users.models import User

router = APIRouter(prefix="/posts", tags=["Работа с постами"])


@router.post('/create_subreddit')
async def create_subreddit(subreddit_data: SubRedditCreateSchema, user: User = Depends(get_current_valid_user)):
    return await SubredditDao.add_forum(subreddit_data.dict(), user)


@router.get('/get_all_subreddit', dependencies=[Depends(get_current_admin_user)])
async def get_subreddit():
    return await SubredditDao.find_all()


@router.get("/get_subreddit")
async def find_subreddit(response_body: SubRedditFindSchema = Depends()):
    return await SubredditDao.find_by_filter(response_body.dict(exclude_none=True))


@router.delete("/delete_subreddit", dependencies=[Depends(get_current_super_admin_user)])
async def delete_subreddit(subreddit_id: int):
    return await SubredditDao.delete_by_id(subreddit_id)


@router.put("/put_subreddit", dependencies=[Depends(get_current_valid_user)])
async def put_subreddit(subreddit_id: int, response_body: SubRedditUpdateSchema):
    return await SubredditDao.update({"id": subreddit_id}, **response_body.dict())


@router.post("/create_post")
async def create_post(post_data: PostCreateSchema, user: User = Depends(get_current_valid_user)):
    return await PostDao.add_forum(post_data.dict(), user)


@router.get("/get_all_posts", dependencies=[Depends(get_current_admin_user)])
async def get_all_posts():
    return await PostDao.find_all()


@router.get("/get_post/")
async def find_post(response_body: PostFindSchema = Depends()):
    return await PostDao.find_by_filter(response_body.dict(exclude_none=True))


@router.put("/update_post", dependencies=[Depends(get_current_valid_user)])
async def update_post(post_id: int, response_body: PostUpdateSchema):
    return await PostDao.update({"id": post_id}, **response_body.dict())


@router.delete("/delete_post/", dependencies=[Depends(get_current_valid_user)])
async def delete_post(post_id: int):
    return await PostDao.delete_by_id(post_id)


@router.post("/create_comment/")
async def create_comment(comment_data: CommentCreateSchema, user: User = Depends(get_current_valid_user)):
    return await CommentDao.add_forum(comment_data.dict(), user)
