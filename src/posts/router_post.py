from fastapi import APIRouter, Depends

from src.posts.dao import PostDao
from src.posts.schemas import PostCreateSchema, PostFindSchema, PostUpdateSchema

from src.users.dependencies import get_current_valid_user, get_current_admin_user
from src.users.models import User

router = APIRouter(prefix="/posts", tags=["Работа с постами"])


@router.post("/create/")
async def create_post(post_data: PostCreateSchema, user: User = Depends(get_current_valid_user)):
    return await PostDao.add_forum(post_data.dict(), user)


@router.get("/get_all/", dependencies=[Depends(get_current_admin_user)])
async def get_all_posts():
    return await PostDao.find_all()


@router.get("/find/")
async def find_post(response_body: PostFindSchema = Depends()):
    return await PostDao.find_by_filter(response_body.dict(exclude_none=True))


@router.put("/update/{post_id}", dependencies=[Depends(get_current_valid_user)])
async def update_post(post_id: int, response_body: PostUpdateSchema):
    return await PostDao.update({"id": post_id}, **response_body.dict())


@router.delete("/delete/{post_id}", dependencies=[Depends(get_current_valid_user)])
async def delete_post(post_id: int):
    return await PostDao.delete_by_id(post_id)
