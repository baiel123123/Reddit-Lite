from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_async_session
from src.users.auth import (
    authenticate_user,
    create_access_token,
    register_user,
    resend_verification_code,
    verify_email,
)
from src.users.dao import UserDao
from src.users.dependencies import (
    get_current_admin_user,
    get_current_user,
    get_current_valid_user,
)
from src.users.models import User
from src.users.schemas import (
    SUserAuth,
    SUserRegister,
    SUserRoleUpdate,
    UserFindSchema,
    UserSchema,
    UserUpdateSchema,
    VerifyEmailSchema,
)

router = APIRouter(prefix="/users", tags=['Работа с пользователями'])


@router.post("/register/")
async def register(user_data: SUserRegister):
    return await register_user(user_data)


@router.post("/login/")
async def auth_user(response: Response, user_data: SUserAuth):
    check = await authenticate_user(email=user_data.email, password=user_data.password)
    if check is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Неверная почта или пароль')
    if check.status == "deleted" or check.status == "banned":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ваш аккаунт удален или забанен!")
    access_token = create_access_token({"sub": str(check.id)})
    response.set_cookie(key="users_access_token", value=access_token, httponly=True)
    return {'access_token': access_token, 'refresh_token': None}


@router.post("/logout/")
async def logout_user(response: Response):
    response.delete_cookie(key="users_access_token")
    return {'message': 'Пользователь успешно вышел из системы'}


@router.post("/verify-email/")
async def verify_email_user(data: VerifyEmailSchema,
                            user: User = Depends(get_current_user),
                            session: AsyncSession = Depends(get_async_session)):
    return await verify_email(data.code, user, session)


@router.post("/resend-code/")
async def resend_code(user: User = Depends(get_current_user),
                      session: AsyncSession = Depends(get_async_session)):
    return await resend_verification_code(user, session)


@router.get("/get_all/", summary="Получить всех пользователей", dependencies=[Depends(get_current_admin_user)])
async def get_all_users() -> list[UserSchema]:
    return await UserDao.find_all()


@router.get("/find/", summary="поиск юзера")
async def find_users(request_body: UserFindSchema = Depends()) -> list[UserSchema]:
    query = await UserDao.find_by_filter(**request_body.dict(exclude_none=True), status="active")
    return query


@router.get("/me/")
async def get_me(user_data: User = Depends(get_current_user)):
    return user_data


@router.put("/role_update/", dependencies=[Depends(get_current_admin_user)])
async def user_role_update(request_body: SUserRoleUpdate):
    if request_body.role_id == 3:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Вы не можете изменить роль администратора")
    return await UserDao.update({"id": request_body.user_id}, role_id=request_body.role_id)


@router.delete("/delete/")
async def user_delete(response: Response, user: User = Depends(get_current_valid_user)):
    await UserDao.user_delete(user)
    response.delete_cookie(key="users_access_token")
    return {"message": "Ваш аккаунт успешно удален"}


@router.delete("/delete_by_id/{user_id}", dependencies=[Depends(get_current_admin_user)])
async def user_delete_by_id(user_id: int):
    user = await UserDao.find_one_or_none_by_id(user_id)
    await UserDao.user_delete(user)
    return {"message": "Аккаунт успешно удален"}


@router.put("/update_user/")
async def update_user(response_body: UserUpdateSchema,
                      user: User = Depends(get_current_valid_user)):
    user = await UserDao.update({"id": user.id}, **response_body.dict(exclude_none=True))
    return user
