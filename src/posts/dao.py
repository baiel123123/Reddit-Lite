from asyncpg import UniqueViolationError
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.config.database import async_session_maker
from src.dao.base import BaseDao
from src.posts.models import Comment, Post, Subreddit, Subscription, Vote
from src.posts.schemas import PostResponse


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
                    await session.refresh(new_instance)
                except IntegrityError:
                    await session.rollback()
                except SQLAlchemyError as e:
                    await session.rollback()
                    return {
                        "error": "An unexpected error occurred while adding the post.",
                        "message": e,
                    }

                return {"data": new_instance}

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
                    vote_query = select(Vote).filter_by(
                        user_id=user.id, comment_id=obj_id
                    )

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
                        new_vote = Vote(
                            user_id=user.id, post_id=post.id, is_upvote=is_upvote
                        )
                    else:
                        new_vote = Vote(
                            user_id=user.id, comment_id=post.id, is_upvote=is_upvote
                        )

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
                except SQLAlchemyError:
                    await session.rollback()
                    return {
                        "error": "An unexpected error occurred while adding the vote."
                    }
                return {"message": "upvoted!", "upvotes": post.upvote}

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
                    vote_query = select(Vote).filter_by(
                        user_id=user.id, comment_id=obj_id
                    )
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
                        return {
                            "error": "An unexpected error occurred while removing the vote."
                        }

                    return {"message": "Vote removed!", "upvotes": post.upvote}

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
                        raise HTTPException(
                            status_code=400, detail="Subreddit already exists"
                        ) from None
                    return {
                        "error": "An unexpected error occurred while adding the post."
                    }
                except SQLAlchemyError:
                    await session.rollback()
                    return {
                        "error": "An unexpected error occurred while adding the post."
                    }

                return {"message": f"{cls.model.__name__} added successfully"}

    @staticmethod
    async def get_subreddit_with_creator(data_id: int):
        async with async_session_maker() as session:
            query = (
                select(Subreddit)
                .filter_by(id=data_id)
                .options(joinedload(Subreddit.created_by))
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()


class PostDao(ForumDao):
    model = Post

    @classmethod
    async def find_my_posts(cls, **filter_by):
        async with async_session_maker() as session:
            query = select(Post).filter_by(**filter_by).order_by(Post.created_at.desc())
            book = await session.execute(query)
            return book.scalars().all()

    @staticmethod
    async def serialize_many_with_votes(
        posts: list[Post], session: AsyncSession, user_id: int
    ) -> list[PostResponse]:
        post_ids = [post.id for post in posts]

        vote_query = await session.execute(
            select(Vote).where(Vote.post_id.in_(post_ids), Vote.user_id == user_id)
        )
        votes = vote_query.scalars().all()
        vote_map = {vote.post_id: vote for vote in votes}

        result = []
        for post in posts:
            vote = vote_map.get(post.id)
            result.append(
                PostResponse(
                    id=post.id,
                    title=post.title,
                    content=post.content,
                    subreddit_id=post.subreddit_id,
                    user_id=post.user_id,
                    upvotes=post.upvote,
                    created_at=post.created_at,
                    user_vote=vote.is_upvote if vote else None,
                )
            )
        return result

    @staticmethod
    async def get_posts_by_subreddit_id(
        subreddit_id: int, limit: int = 20, offset: int = 20
    ):
        async with async_session_maker() as session:
            query = (
                select(Post)
                .filter_by(subreddit_id=subreddit_id)
                .order_by(Post.created_at)
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(query)
            return result.scalars().all()


class CommentDao(ForumDao):
    model = Comment

    @classmethod
    async def get_comments_by_post(cls, post_id, offset: int = 0, limit: int = 20):
        async with async_session_maker() as session:
            query = (
                select(cls.model)
                .filter_by(post_id=post_id)
                .offset(offset)
                .limit(limit)
                .order_by(Comment.created_at.desc())
            )
            book = await session.execute(query)
            return book.scalars().all()

    @staticmethod
    async def add_reply(data: dict, user, session: AsyncSession) -> Comment:
        new_comment = Comment(**data, user_id=user.id)
        session.add(new_comment)
        await session.commit()
        await session.refresh(new_comment)
        return new_comment


class VoteDao(ForumDao):
    model = Vote

    @classmethod
    async def get_user_votes_for_comments(cls, user_id, comment_ids: list[int]):
        async with async_session_maker() as session:
            query = select(Vote).filter(
                Vote.user_id == user_id, Vote.comment_id.in_(comment_ids)
            )
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def get_post_votes_by_user(user_id: int, post_ids: list[int]):
        async with async_session_maker() as session:
            query = select(Vote).where(
                Vote.user_id == user_id, Vote.post_id.in_(post_ids)
            )
            result = await session.execute(query)
            votes = result.scalars().all()

        return [
            {"target_id": vote.post_id, "is_upvote": vote.is_upvote} for vote in votes
        ]


class SubscriptionDao(ForumDao):
    model = Subscription

    @classmethod
    async def find_all_subscriptions(cls, filter_by):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            book = await session.execute(query)
            return book.scalars().all()
