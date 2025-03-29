from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.database import Base, int_pk
from src.users.models import User


class Subreddit(Base):
    id: Mapped[int_pk] = mapped_column(index=True)
    name: Mapped[str] = mapped_column(String(25), unique=True)
    description: Mapped[str] = mapped_column(String(50))

    users = relationship(User, secondary="usersubredditassociations", back_populates="subreddits")
    posts = relationship("Post", back_populates="subreddit", cascade="all, delete-orphan")

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, name='{self.name}')"


class UserSubredditAssociation(Base):
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    subreddit_id: Mapped[int] = mapped_column(ForeignKey("subreddits.id"), primary_key=True)


class Post(Base):
    id: Mapped[int_pk] = mapped_column(index=True)
    title: Mapped[str] = mapped_column(String(300), index=True)
    content: Mapped[str] = mapped_column(String(40000), nullable=True)
    upvote: Mapped[int] = mapped_column(default=0)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    subreddit_id: Mapped[int] = mapped_column(ForeignKey("subreddits.id", ondelete="CASCADE"))
    
    user = relationship(User, back_populates="posts")
    subreddit = relationship("Subreddit", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id})"


class Comment(Base):
    id: Mapped[int_pk] = mapped_column(index=True)
    content: Mapped[str] = mapped_column(String(4000), nullable=False)
    upvote: Mapped[int] = mapped_column(default=0)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"))

    user = relationship(User, back_populates="comments")
    post = relationship("Post", back_populates="comments")

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id})"


class Vote(Base):
    id: Mapped[int_pk] = mapped_column(index=True)
    user_id: Mapped[int] = mapped_column(index=True)