from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt

from src.config.settings import get_auth_data, get_email_settings
from src.users.dao import UserDao
from src.users.models import User

email_settings = get_email_settings()


def get_token(request: Request):
    token = request.cookies.get("users_access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token not found"
        )
    return token


async def get_current_user_or_none(token: str = Depends(get_token)):
    try:
        auth_data = get_auth_data()
        payload = jwt.decode(
            token, auth_data["secret_key"], algorithms=[auth_data["algorithm"]]
        )
    except JWTError:
        return None

    expire = payload.get("exp")
    expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)
    if (not expire) or (expire_time < datetime.now(timezone.utc)):
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user = await UserDao.find_one_or_none_by_id(int(user_id))
    if not user:
        return None

    return user


async def get_current_user(token: str = Depends(get_token)):
    try:
        auth_data = get_auth_data()
        payload = jwt.decode(
            token, auth_data["secret_key"], algorithms=[auth_data["algorithm"]]
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен не валидный!"
        ) from None

    expire = payload.get("exp")
    expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)
    if (not expire) or (expire_time < datetime.now(timezone.utc)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен истек"
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Не найден ID пользователя"
        )

    user = await UserDao.find_one_or_none_by_id(int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    return user


async def get_current_valid_user(current_user: User = Depends(get_current_user)):
    if current_user.status == "banned" or current_user.status == "deleted":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ваш аккаунт забанен или удален!",
        )
    if (
        current_user.is_verified
        or current_user.role_id == 2
        or current_user.role_id == 3
    ):
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Вы не авторизовались!"
    )


async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role_id >= 2:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав!"
    )


async def get_current_super_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role_id == 3:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав!"
    )
