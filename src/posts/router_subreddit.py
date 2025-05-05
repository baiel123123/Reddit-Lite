from fastapi import APIRouter, Depends, HTTPException

from src.posts.dao import SubredditDao, SubscriptionDao
from src.posts.schemas import (
    SubRedditCreateSchema,
    SubRedditFindSchema,
    SubRedditUpdateSchema,
)
from src.users.dependencies import (
    get_current_admin_user,
    get_current_super_admin_user,
    get_current_valid_user,
)
from src.users.models import User

router = APIRouter(prefix="/subreddit", tags=["Работа с сабреддитами"])


@router.post('/create/')
async def create_subreddit(subreddit_data: SubRedditCreateSchema, user: User = Depends(get_current_valid_user)):
    return await SubredditDao.add_subreddit(subreddit_data.dict(), user)


@router.get('/get_all/', dependencies=[Depends(get_current_admin_user)])
async def get_all_subreddit():
    return await SubredditDao.find_all()


@router.get("/find/")
async def find_subreddit(response_body: SubRedditFindSchema = Depends()):
    return await SubredditDao.find_by_filter(**response_body.dict(exclude_none=True))


@router.put("/update/{subreddit_id}", dependencies=[Depends(get_current_valid_user)])
async def update_subreddit(subreddit_id: int, response_body: SubRedditUpdateSchema):
    return await SubredditDao.update({"id": subreddit_id}, **response_body.dict())


@router.delete("/delete/{subreddit_id}", dependencies=[Depends(get_current_super_admin_user)])
async def delete_subreddit(subreddit_id: int):
    return await SubredditDao.delete_by_id(subreddit_id)


@router.post("/create_subscribe/{subreddit_id}")
async def create_subscription(subreddit_id: int, user: User = Depends(get_current_valid_user)):
    return await SubscriptionDao.add_forum({"subreddit_id": subreddit_id}, user)


@router.get("/get_all_subscriptions/")
async def get_all_subscriptions(user: User = Depends(get_current_valid_user)):
    return await SubscriptionDao.find_all_subscriptions({"user": user})


@router.delete("/delete_subscription/{subscription_id}", dependencies=[Depends(get_current_valid_user)])
async def delete_subscription(subscription_id: int, user: User = Depends(get_current_valid_user)):
    subscription = await SubscriptionDao.find_one_or_none_by_id(subscription_id)

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if subscription.user_id != user.id:
        raise HTTPException(status_code=403, detail="You are not the owner of this subscription")

    await SubscriptionDao.delete_by_id(subscription_id)
    return {"message": "Subscription deleted successfully"}
