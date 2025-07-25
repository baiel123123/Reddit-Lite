from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import get_auth_data
from src.tasks.send_email import send_verification_email
from src.users.dao import UserDao
from src.users.models import User
from src.users.schemas import SUserRegister
from src.utilts import generate_verification_code

auth_data = get_auth_data()

SECRET_KEY = auth_data["secret_key"]
ALGORITHM = auth_data["algorithm"]
ACCESS_TOKEN_EXPIRE_MINUTES = auth_data["access_token_expire_minutes"]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def authenticate_user(email: EmailStr, password: str):
    user = await UserDao.find_one_or_none(email=email)
    if (
        not user
        or verify_password(plain_password=password, hashed_password=user.password)
        is False
    ):
        return None
    return user


async def register_user(user_data: SUserRegister):
    existing_user = await UserDao.find_one_or_none(email=user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=400, detail="Пользователь с таким email уже существует"
        )

    hashed_password = get_password_hash(user_data.password)
    verification_code = generate_verification_code()

    await UserDao.add(
        username=user_data.username,
        email=user_data.email,
        password=hashed_password,
        gender=user_data.gender,
        date_of_birth=user_data.date_of_birth,
        is_verified=False,
        verification_code=verification_code,
        verification_expires=datetime.now() + timedelta(minutes=10),
    )

    send_verification_email.apply_async(args=[user_data.email, verification_code])

    return {"message": "Код подтверждения отправлен на email"}


async def verify_email(code: str, user: User, session: AsyncSession):
    if not user:
        raise HTTPException(status_code=400, detail="Пользователь не найден")

    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email уже подтвержден")

    if user.verification_code != code:
        raise HTTPException(status_code=400, detail="Неверный код подтверждения")

    if user.verification_expires < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Код подтверждения истек")

    user.is_verified = True
    user.verification_code = None
    user.verification_expires = None

    await session.merge(user)
    await session.commit()

    return {"message": "Email успешно подтвержден", "success": True}


RESEND_COOLDOWN_SECONDS = 60


async def resend_verification_code(user: User, session: AsyncSession):
    now = datetime.now(timezone.utc)

    if user.is_verified:
        return {"message": "Email уже подтвержден", "success": False}

    if user.resend_cooldown and user.resend_cooldown > now:
        seconds_left = int((user.resend_cooldown - now).total_seconds())
        raise HTTPException(
            status_code=429,
            detail=f"Подождите {seconds_left} сек. перед повторной отправкой",
        )

    new_code = generate_verification_code()
    user.verification_code = new_code
    user.verification_expires = now + timedelta(minutes=10)
    user.resend_cooldown = now + timedelta(seconds=RESEND_COOLDOWN_SECONDS)

    await session.merge(user)
    await session.commit()

    send_verification_email.apply_async(args=[user.email, new_code])

    return {"message": "Новый код подтверждения отправлен на email", "success": True}
