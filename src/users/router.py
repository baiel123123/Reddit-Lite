from fastapi import APIRouter, Depends, HTTPException, status, Response

from src.users.auth import get_password_hash, authenticate_user, create_access_token
from src.users.dao import UserDao
from src.users.dependencies import get_current_user, get_current_admin_user
from src.users.models import User
from src.users.schemas import UserSchema, UserFindSchema, SUserRegister, SUserAuth, SUserRoleUpdate

router = APIRouter(prefix="/users", tags=['Работа с пользователями'])


@router.get("/", summary="Получить всех пользователей")
async def get_all_users(user: User = Depends(get_current_admin_user)) -> list[UserSchema]:
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


@router.post("/login/")
async def auth_user(response: Response, user_data: SUserAuth):
    check = await authenticate_user(email=user_data.email, password=user_data.password)
    if check is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Неверная почта или пароль')
    access_token = create_access_token({"sub": str(check.id)})
    response.set_cookie(key="users_access_token", value=access_token, httponly=True)
    return {'access_token': access_token, 'refresh_token': None}


@router.get("/me/")
async def get_me(user_data: User = Depends(get_current_user)):
    return user_data


@router.post("/logout/")
async def logout_user(response: Response):
    response.delete_cookie(key="users_access_token")
    return {'message': 'Пользователь успешно вышел из системы'}


@router.put("/user_role_update/")
async def user_role_update(request_body: SUserRoleUpdate):
    return await UserDao.update(request_body.user_id, role_id=request_body.role_id)
