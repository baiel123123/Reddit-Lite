from fastapi import HTTPException, status
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError

from src.config.database import async_session_maker
from src.dao.base import BaseDao
from src.users.models import User


class UserDao(BaseDao):
    model = User

    @classmethod
    async def update_role(cls, user_id, role_id):
        async with async_session_maker() as session:
            async with session.begin():
                query = (
                    update(User)
                    .where(User.id == user_id)
                    .values(role_id=role_id)
                    .returning(User)
                )
                result = await session.execute(query)
                try:
                    await session.commit()
                except SQLAlchemyError as e:
                    await session.rollback()
                    raise e
                return result.scalars().first()

    @classmethod
    async def user_delete(cls, user):
        async with async_session_maker() as session:
            async with session.begin():
                if user.status == "active":
                    user.status = "deleted"
                else:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Вы не можете удалить аккаунт")
                await session.merge(user)
                try:
                    await session.commit()
                except SQLAlchemyError as e:
                    await session.rollback()
                    raise e