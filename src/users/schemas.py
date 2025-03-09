from datetime import datetime
from typing import Optional

from pydantic import validator, BaseModel, EmailStr, Field


class UserSchema(BaseModel):
    id: int
    username: str
    nickname: Optional[str]
    email: str
    gender: str
    about_me: Optional[str]
    date_of_birth: datetime

    # @validator("date_of_birth")
    # def validate_date_of_birth(cls, value):
    #     if value and value >= datetime.now():
    #         raise ValueError('Дата рождения должна быть в прошлом')
    #     return value


class UserFindSchema(BaseModel):
    id: Optional[int] = None
    username: Optional[str] = None
    email: Optional[str] = None


class SUserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="username до 50")
    email: EmailStr = Field(..., min_length=5, max_length=255, description="Электронная почта")
    date_of_birth: datetime = Field(..., description="Дата рождения в виде YYYY-MM-DD")
    gender: str = Field(..., description="Выберите пол, male, female or other")
    password: str = Field(..., min_length=5, max_length=50, description="Пароль, от 5 до 50 знаков")
