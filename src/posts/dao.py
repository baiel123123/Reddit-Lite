from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.config.database import async_session_maker
from src.dao.base import BaseDao
from src.posts.models import Post, Subreddit, Comment


class ForumDao(BaseDao):
    model = None

    @classmethod
    async def add_forum(cls, data, user):
        async with async_session_maker() as session:
            async with session.begin():
                new_instance = cls.model(**data)
                new_instance.user = user

                session.add(new_instance)
                try:
                    await session.commit()
                except IntegrityError:
                    await session.rollback()
                except SQLAlchemyError as e:
                    await session.rollback()
                    return {"error": "An unexpected error occurred while adding the post."}

                return {"message": f"{cls.model.__name__} added successfully"}


class SubredditDao(ForumDao):
    model = Subreddit


class PostDao(ForumDao):
    model = Post


class CommentDao(ForumDao):
    model = Comment
