from fastapi import HTTPException
from sqlalchemy import select, delete as sqlalchemy_delete
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.config.database import async_session_maker
from src.dao.base import BaseDao
from src.posts.models import Post, Subreddit, Comment, Vote, Subscription
from asyncpg import UniqueViolationError


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

    @classmethod
    async def up_vote(cls, obj_id, is_upvote, user):
        async with async_session_maker() as session:
            async with session.begin():
                post = await session.execute(select(cls.model).filter_by(id=obj_id))
                post = post.scalars().first()

                if not post:
                    return {"error": "Post or comment not found."}

                if isinstance(post, Post):
                    vote_query = select(Vote).filter_by(user_id=user.id, post_id=obj_id)
                else:
                    vote_query = select(Vote).filter_by(user_id=user.id, comment_id=obj_id)

                vote_result = await session.execute(vote_query)
                vote = vote_result.scalars().first()

                if vote:
                    if is_upvote != vote.is_upvote:
                        if is_upvote:
                            post.upvote += 2
                        else:
                            post.upvote -= 2
                        vote.is_upvote = is_upvote
                else:
                    if isinstance(post, Post):
                        new_vote = Vote(user_id=user.id, post_id=post.id, is_upvote=is_upvote)
                    else:
                        new_vote = Vote(user_id=user.id, comment_id=post.id, is_upvote=is_upvote)

                    if is_upvote:
                        post.upvote += 1
                        new_vote.is_upvote = True
                    else:
                        post.upvote -= 1
                        new_vote.is_upvote = False
                    session.add(new_vote)

                try:
                    await session.commit()
                except IntegrityError:
                    await session.rollback()
                except SQLAlchemyError as e:
                    await session.rollback()
                    return {"error": "An unexpected error occurred while adding the vote."}
                return {"message": f"upvoted!"}

    @classmethod
    async def remove_vote(cls, obj_id, user):
        async with async_session_maker() as session:
            async with session.begin():
                post = await session.execute(select(cls.model).filter_by(id=obj_id))
                post = post.scalars().first()
                if not post:
                    return {"error": "Post not found."}

                if isinstance(post, Post):
                    vote_query = select(Vote).filter_by(user_id=user.id, post_id=obj_id)
                else:
                    vote_query = select(Vote).filter_by(user_id=user.id, comment_id=obj_id)
                vote_result = await session.execute(vote_query)
                vote = vote_result.scalars().first()

                if vote:
                    if vote.is_upvote:
                        post.upvote -= 1
                    else:
                        post.upvote += 1

                    await session.delete(vote)

                    try:
                        await session.commit()
                    except SQLAlchemyError:
                        await session.rollback()
                        return {"error": "An unexpected error occurred while removing the vote."}

                    return {"message": "Vote removed!"}

                return {"error": "Vote not found."}


class SubredditDao(ForumDao):
    model = Subreddit

    @classmethod
    async def add_subreddit(cls, data, user):
        async with async_session_maker() as session:
            async with session.begin():
                new_instance = cls.model(**data)
                new_instance.created_by = user

                session.add(new_instance)
                try:
                    await session.commit()
                except IntegrityError as e:
                    await session.rollback()
                    if isinstance(e.orig, UniqueViolationError):
                        raise HTTPException(status_code=400, detail="Subreddit already exists")
                    return {"error": "An unexpected error occurred while adding the post."}
                except SQLAlchemyError as e:
                    await session.rollback()
                    return {"error": "An unexpected error occurred while adding the post."}

                return {"message": f"{cls.model.__name__} added successfully"}


class PostDao(ForumDao):
    model = Post


class CommentDao(ForumDao):
    model = Comment


class VoteDao(ForumDao):
    model = Vote


class SubscriptionDao(ForumDao):
    model = Subscription
