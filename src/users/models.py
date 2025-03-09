from datetime import datetime

from sqlalchemy import text, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from src.config.database import Base, str_uniq, int_pk

from enum import Enum as PyEnum

from sqlalchemy import Enum


class SocialPlatform(PyEnum):
    CUSTOM = "Custom"
    FACEBOOK = "Facebook"
    TWITTER = "Twitter"
    INSTAGRAM = "Instagram"
    YOUTUBE = "YouTube"
    TELEGRAM = "Telegram"
    TWITCH = "Twitch"
    DISCORD = "Discord"


class GenderEnum(str, PyEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class SocialLink(Base):
    id: Mapped[int_pk]
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    platform: Mapped[SocialPlatform] = mapped_column(Enum(SocialPlatform), nullable=False)
    url: Mapped[str] = mapped_column(String(255), nullable=False)

    user = relationship("User", back_populates="social_links")


class User(Base):
    id: Mapped[int_pk]
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nickname: Mapped[str] = mapped_column(String(50), nullable=True)
    email: Mapped[str_uniq] = mapped_column(String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    gender: Mapped[GenderEnum] = mapped_column(Enum(GenderEnum), nullable=False)
    about_me: Mapped[str] = mapped_column(String(255), nullable=True)
    date_of_birth: Mapped[datetime]

    is_user: Mapped[bool] = mapped_column(default=True, server_default=text('true'), nullable=False)
    is_admin: Mapped[bool] = mapped_column(default=False, server_default=text('false'), nullable=False)
    is_super_admin: Mapped[bool] = mapped_column(default=False, server_default=text('false'), nullable=False)

    social_links = relationship("SocialLink", back_populates="user")

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id})"

    @validates('password')
    def validate_password(self, key, password):
        if 255 > len(password) < 8:
            raise ValueError("Пароль должен быть не менее 8 символов и не больше 255")
        return password

