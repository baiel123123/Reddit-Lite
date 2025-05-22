from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator

from src.users.models import GenderEnum, UserStatus


class UserSchema(BaseModel):
    id: int
    username: str
    nickname: Optional[str]
    email: str
    gender: str
    about_me: Optional[str]
    date_of_birth: datetime
    password: Optional[str]
    status: UserStatus


class UserFindSchema(BaseModel):
    id: Optional[int] = None
    username: Optional[str] = None
    email: Optional[str] = None


class SUserRegister(BaseModel):
    username: str = Field(
        ..., min_length=3, max_length=50, description="username до 50"
    )
    email: EmailStr = Field(
        ..., min_length=5, max_length=255, description="Электронная почта"
    )
    date_of_birth: datetime = Field(..., description="Дата рождения в виде YYYY-MM-DD")
    gender: str = Field(..., description="Выберите пол, male, female or other")
    password: str = Field(
        ..., min_length=5, max_length=50, description="Пароль, от 5 до 50 знаков"
    )


class SUserAuth(BaseModel):
    email: EmailStr = Field(..., description="Электронная почта")
    password: str = Field(
        ..., min_length=5, max_length=50, description="Пароль, от 5 до 50 знаков"
    )


class SUserRoleUpdate(BaseModel):
    user_id: int
    role_id: int


class VerifyEmailSchema(BaseModel):
    code: str


class UserUpdateSchema(BaseModel):
    nickname: Optional[str] = Field(None, min_length=3, max_length=50)
    gender: Optional[GenderEnum] = None
    about_me: Optional[str] = Field(None, max_length=255)
    date_of_birth: Optional[datetime] = None

    @validator("*", pre=True)
    def empty_str_to_none(cls, v):
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


class TokenRefreshRequest(BaseModel):
    refresh_token: str
