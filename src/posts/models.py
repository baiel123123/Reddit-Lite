from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.database import Base, int_pk
from src.users.models import User


class Subreddit(Base):
    id: Mapped[int_pk]
    name: Mapped[str] = mapped_column(String(25), unique=True)
    description: Mapped[str] = mapped_column(String(50))
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=True)

    created_by = relationship('User', back_populates='created_subreddits')
    subscribers = relationship('Subscription', back_populates='subreddit', cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="subreddit", cascade="all, delete-orphan")

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, name='{self.name}')"


class Subscription(Base):
    id: Mapped[int_pk]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    subreddit_id: Mapped[int] = mapped_column(ForeignKey("subreddits.id", ondelete="CASCADE"))

    __table_args__ = (
        UniqueConstraint("user_id", "subreddit_id", name="uix_user_id_subreddit_id"),
    )

    user = relationship('User', back_populates='subscriptions')
    subreddit = relationship('Subreddit', back_populates='subscribers')


class Post(Base):
    id: Mapped[int_pk]
    title: Mapped[str] = mapped_column(String(300))
    content: Mapped[str] = mapped_column(String(40000), nullable=True)
    upvote: Mapped[int] = mapped_column(default=0)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete='SET NULL'), index=True)
    subreddit_id: Mapped[int] = mapped_column(ForeignKey("subreddits.id", ondelete="CASCADE"), index=True)
    
    user = relationship(User, back_populates="posts")
    subreddit = relationship("Subreddit", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    votes = relationship("Vote", back_populates="post", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id})"


class Comment(Base):
    id: Mapped[int_pk] = mapped_column(index=True)
    content: Mapped[str] = mapped_column(String(4000), nullable=False)
    upvote: Mapped[int] = mapped_column(default=0)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"))

    votes = relationship("Vote", back_populates="comment", cascade="all, delete-orphan")
    user = relationship(User, back_populates="comments")
    post = relationship("Post", back_populates="comments")

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id})"


class Vote(Base):
    id: Mapped[int_pk]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), nullable=True)
    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)
    is_upvote: Mapped[bool] = mapped_column(nullable=False)

    user = relationship("User", back_populates="votes")
    post = relationship("Post", back_populates="votes")
    comment = relationship("Comment", back_populates="votes")

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id})"
