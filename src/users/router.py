from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from src.config.database import get_async_session
from src.users.auth import (
    auth_data,
    authenticate_user,
    create_access_token,
    create_refresh_token,
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
    TokenRefreshRequest,
    UserFindSchema,
    UserSchema,
    UserUpdateSchema,
    VerifyEmailSchema,
)

router = APIRouter(prefix="/users", tags=["users"])

SECRET_KEY = auth_data["secret_key"]
ALGORITHM = auth_data["algorithm"]
ACCESS_TOKEN_EXPIRE_MINUTES = auth_data["access_token_expire_minutes"]


@router.post("/register/")
async def register(user_data: SUserRegister):
    return await register_user(user_data)


@router.post("/login/")
async def auth_user(response: Response, user_data: SUserAuth):
    check = await authenticate_user(email=user_data.email, password=user_data.password)
    if check is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверная почта или пароль"
        )
    if check.status == "deleted" or check.status == "banned":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ваш аккаунт удален или забанен!",
        )
    access_token = create_access_token({"sub": str(check.id)})
    refresh_token = create_refresh_token(data={"sub": str(check.id)})
    response.set_cookie(key="users_access_token", value=access_token, httponly=True)
    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post("/logout/")
async def logout_user(response: Response):
    response.delete_cookie(key="users_access_token")
    return {"message": "Пользователь успешно вышел из системы"}


@router.post("/verify-email/")
async def verify_email_user(
    data: VerifyEmailSchema,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    return await verify_email(data.code, user, session)


@router.post("/resend-code/")
async def resend_code(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    return await resend_verification_code(user, session)


@router.get(
    "/get_all/",
    summary="Получить всех пользователей",
    dependencies=[Depends(get_current_admin_user)],
)
async def get_all_users():
    return await UserDao.find_all()


@router.get("/find/", summary="поиск юзера")
async def find_users(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0),
    request_body: UserFindSchema = Depends(),
) -> list[UserSchema]:
    request_body = request_body.dict(exclude_none=True)

    if not request_body:
        return []

    query = await UserDao.find_by_filter(limit, offset, **request_body, status="active")
    return query


@router.get("/me/")
async def get_me(user_data: User = Depends(get_current_user)):
    return user_data


@router.put("/role_update/", dependencies=[Depends(get_current_admin_user)])
async def user_role_update(request_body: SUserRoleUpdate):
    if request_body.role_id == 3:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не можете изменить роль администратора",
        )
    return await UserDao.update(
        {"id": request_body.user_id}, role_id=request_body.role_id
    )


@router.delete("/delete/")
async def user_delete(response: Response, user: User = Depends(get_current_valid_user)):
    await UserDao.user_delete(user)
    response.delete_cookie(key="users_access_token")
    return {"message": "Ваш аккаунт успешно удален"}


@router.delete(
    "/delete_by_id/{user_id}", dependencies=[Depends(get_current_admin_user)]
)
async def user_delete_by_id(user_id: int):
    user = await UserDao.find_one_or_none_by_id(user_id)
    await UserDao.user_delete(user)
    return {"message": "Аккаунт успешно удален"}


@router.put("/update_user/")
async def update_user(
    response_body: UserUpdateSchema, user: User = Depends(get_current_valid_user)
):
    user = await UserDao.update(
        {"id": user.id}, **response_body.dict(exclude_none=True)
    )
    return user


@router.post("/refresh-token/")
async def refresh_token(request: TokenRefreshRequest, response: Response):
    try:
        payload = jwt.decode(request.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Некорректный refresh token")
    except JWTError as err:
        raise HTTPException(
            status_code=401, detail="Некорректный или просроченный refresh token"
        ) from err

    user = await UserDao.find_one_or_none_by_id(int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    response.set_cookie(key="users_access_token", value=access_token, httponly=True)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/avatar/{user_id}", response_class=RedirectResponse)
async def get_avatar(user_id: str):
    url = f"https://api.dicebear.com/9.x/pixel-art/svg?seed={user_id}"
    return RedirectResponse(url)
