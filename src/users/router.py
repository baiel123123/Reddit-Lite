from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_async_session
from src.users.auth import (authenticate_user, create_access_token, register_user,
                            verify_email, resend_verification_code)
from src.users.dao import UserDao
from src.users.dependencies import get_current_user, get_current_admin_user, get_current_valid_user
from src.users.models import User
from src.users.schemas import UserSchema, UserFindSchema, SUserRegister, SUserAuth, SUserRoleUpdate, VerifyEmailSchema

router = APIRouter(prefix="/users", tags=['Работа с пользователями'])


@router.post("/register")
async def register(user_data: SUserRegister):
    return await register_user(user_data)


@router.post("/login/")
async def auth_user(response: Response, user_data: SUserAuth):
    check = await authenticate_user(email=user_data.email, password=user_data.password)
    if check is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Неверная почта или пароль')
    access_token = create_access_token({"sub": str(check.id)})
    response.set_cookie(key="users_access_token", value=access_token, httponly=True)
    return {'access_token': access_token, 'refresh_token': None}


@router.post("/logout/")
async def logout_user(response: Response):
    response.delete_cookie(key="users_access_token")
    return {'message': 'Пользователь успешно вышел из системы'}


@router.post("/verify-email-user")
async def verify_email_user(data: VerifyEmailSchema,
                            user: User = Depends(get_current_user),
                            session: AsyncSession = Depends(get_async_session)):
    return await verify_email(data.code, user, session)


@router.post("/resend-code")
async def resend_code(user: User = Depends(get_current_user),
                      session: AsyncSession = Depends(get_async_session)):
    return await resend_verification_code(user, session)


@router.get("/", summary="Получить всех пользователей", dependencies=[Depends(get_current_admin_user)])
async def get_all_users() -> list[UserSchema]:
    return await UserDao.find_all()


@router.get("/find_user", summary="поиск юзера")
async def find_users(request_body: UserFindSchema = Depends()) -> list[UserSchema]:
    query = await UserDao.find_by_filter(request_body.dict(exclude_none=True))
    return query


@router.get("/me/")
async def get_me(user_data: User = Depends(get_current_user)):
    return user_data


@router.put("/user_role_update/", dependencies=[Depends(get_current_admin_user)])
async def user_role_update(request_body: SUserRoleUpdate):
    if request_body.role_id == 3:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Вы не можете изменить роль администратора")
    return await UserDao.update({"id": request_body.user_id}, role_id=request_body.role_id)
