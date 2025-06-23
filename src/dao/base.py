from alembic.util import err
from fastapi import HTTPException
from sqlalchemy import String, cast, select, update
from sqlalchemy import delete as sqlalchemy_delete
from sqlalchemy.exc import DataError, IntegrityError, SQLAlchemyError

from src.config.database import async_session_maker


class BaseDao:
    model = None

    @classmethod
    async def find_all(cls):
        async with async_session_maker() as session:
            query = select(cls.model).order_by(cls.model.created_at.desc())
            book = await session.execute(query)
            return book.scalars().all()

    @classmethod
    async def find_by_filter(cls, limit: int, offset: int, **filter_by):
        async with async_session_maker() as session:
            if not filter_by:
                return []
            query = select(cls.model)
            for field_name, search_value in filter_by.items():
                column = getattr(cls.model, field_name)
                if isinstance(search_value, str):
                    query = query.where(cast(column, String).ilike(f"%{search_value}%"))
                else:
                    query = query.where(column == search_value)
            query = query.offset(offset).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def find_one_or_none(cls, **filter_by):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def find_one_or_none_by_id(cls, data_id: int):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(id=data_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def add(cls, **values):
        async with async_session_maker() as session:
            async with session.begin():
                new_instance = cls.model(**values)
                session.add(new_instance)
                try:
                    await session.commit()
                except IntegrityError as e:
                    await session.rollback()
                    raise e
                except DataError:
                    await session.rollback()
                    raise HTTPException(
                        status_code=400,
                        detail="Некорректные данные (например, слишком длинный email)",
                    ) from err
                except SQLAlchemyError as e:
                    await session.rollback()
                    raise e
                return new_instance

    @classmethod
    async def update(cls, filter_by, **values):
        async with async_session_maker() as session:
            async with session.begin():
                query = (
                    update(cls.model)
                    .where(*[getattr(cls.model, k) == v for k, v in filter_by.items()])
                    .values(**values)
                    .execution_options(synchronize_session="fetch")
                    .returning(cls.model)
                )
                result = await session.execute(query)
                try:
                    await session.commit()
                except SQLAlchemyError as e:
                    await session.rollback()
                    raise e
                return result.scalars().one_or_none()

    @classmethod
    async def delete_by_id(cls, obj_id: int):
        async with async_session_maker() as session:
            async with session.begin():
                query = (
                    sqlalchemy_delete(cls.model)
                    .filter_by(id=obj_id)
                    .returning(cls.model)
                )
                result = await session.execute(query)
                try:
                    await session.commit()
                except SQLAlchemyError as e:
                    await session.rollback()
                    raise e
                return result.scalars().one_or_none()
