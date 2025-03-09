from fastapi import APIRouter, Depends, HTTPException, status

from src.users.auth import get_password_hash
from src.users.dao import UserDao
from src.users.schemas import UserSchema, UserFindSchema, SUserRegister

router = APIRouter(prefix='/users', tags=['Работа с пользователями'])


@router.get("/", summary="Получить всех пользователей")
async def get_all_users() -> list[UserSchema]:
    return await UserDao.find_all()


@router.get("/find_user", summary="поиск юзера")
async def find_users(request_body: UserFindSchema = Depends()) -> list[UserSchema]:
    query = await UserDao.find_by_filter(request_body.dict(exclude_none=True))
    return query


@router.post("/register/")
async def register_user(user_data: SUserRegister) -> dict:
    user = await UserDao.find_one_or_none(email=user_data.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Пользователь уже существует'
        )
    user_dict = user_data.dict()
    user_dict['password'] = get_password_hash(user_data.password)
    await UserDao.add(**user_dict)
    return {'message': 'Вы успешно зарегистрированы!'}
