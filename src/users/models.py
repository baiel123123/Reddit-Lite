from datetime import datetime

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from src.config.database import Base, int_pk

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


class Role(Base):
    id: Mapped[int_pk]
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    user = relationship("User", back_populates="role")


class User(Base):
    id: Mapped[int_pk]
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nickname: Mapped[str] = mapped_column(String(50), nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    gender: Mapped[GenderEnum] = mapped_column(Enum(GenderEnum), nullable=False)
    about_me: Mapped[str] = mapped_column(String(255), nullable=True)
    date_of_birth: Mapped[datetime] = mapped_column(nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey('roles.id'), nullable=False, default=1, server_default="1")
    is_verified: Mapped[bool] = mapped_column(default=False, server_default="false")
    verification_code: Mapped[str] = mapped_column(nullable=True)
    verification_expires: Mapped[datetime] = mapped_column(nullable=True)
    # is_deleted: Mapped[bool] = mapped_column(default=False, server_default="false")

    role = relationship("Role", back_populates="user")
    social_links = relationship("SocialLink", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    posts = relationship("Post", back_populates="user")
    votes = relationship("Vote", back_populates="user")

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id})"

    @validates('password')
    def validate_password(self, key, password):
        if 255 < len(password) or len(password) < 8:
            raise ValueError("Пароль должен быть не менее 8 символов и не больше 255")
        return password

    # @classmethod
    # def soft_delete(cls, session, user_id: int):
    #     user = session.query(cls).get(user_id)
    #     if user:
    #         user.is_deleted = True
    #         session.commit()
    #
    # @classmethod
    # def restore(cls, session, user_id: int):
    #     user = session.query(cls).get(user_id)
    #     if user:
    #         user.is_deleted = False
    #         session.commit()
