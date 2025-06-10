from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from src.config.database import async_session_maker
from src.posts.dao import CommentDao, PostDao, VoteDao
from src.posts.models import Comment
from src.posts.schemas import CommentCreateSchema, CommentUpdateSchema
from src.users.dependencies import (
    get_current_admin_user,
    get_current_user_or_none,
    get_current_valid_user,
)
from src.users.models import User

router = APIRouter(prefix="/comments", tags=["Работа с комментариями"])


@router.post("/create/", status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment_data: CommentCreateSchema,
    user: User = Depends(get_current_valid_user),
):
    return await CommentDao.add_forum(comment_data.dict(), user)


@router.post("/reply_to_comment/{comment_id}")
async def reply_to_comment(
    comment_id: int,
    comment_data: CommentCreateSchema,
    user: User = Depends(get_current_valid_user),
):
    parent_comment = await CommentDao.find_one_or_none_by_id(comment_id)
    if not parent_comment:
        raise HTTPException(status_code=404, detail="Комментарий для ответа не найден")

    data = comment_data.dict()
    data["parent_comment_id"] = comment_id

    new_comment = await CommentDao.add_forum(data, user)
    return new_comment


@router.get("/get_all/", dependencies=[Depends(get_current_admin_user)])
async def get_all_comments():
    return await CommentDao.find_all()


@router.put("/{comment_id}", dependencies=[Depends(get_current_valid_user)])
async def comment_update(
    comment_id: int,
    response_body: CommentUpdateSchema,
    current_user: User = Depends(get_current_valid_user),
):
    comment = await CommentDao.find_one_or_none_by_id(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Комментарий не найден")
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Нет доступа к редактированию чужого комментария"
        )

    updated_comment = await CommentDao.update(
        {"id": comment_id}, **response_body.dict()
    )
    return updated_comment


@router.delete("/delete/{comment_id}", dependencies=[Depends(get_current_valid_user)])
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_valid_user),
):
    comment = await CommentDao.find_one_or_none_by_id(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Комментарий не найден")

    if comment.user_id != current_user.id and current_user.role not in (2, 3):
        raise HTTPException(
            status_code=403, detail="Нет прав на удаление этого комментария"
        )

    await CommentDao.delete_by_id(comment_id)
    return {"detail": "Комментарий удалён"}


@router.post("/upvote/{comment_id}", dependencies=[Depends(get_current_valid_user)])
async def upvote(
    comment_id: int,
    is_upvote: bool,
    user: User = Depends(get_current_valid_user),
):
    return await CommentDao.up_vote(comment_id, is_upvote, user)


@router.post(
    "/delete_upvote/{comment_id}", dependencies=[Depends(get_current_valid_user)]
)
async def delete_upvote(
    comment_id: int,
    user: User = Depends(get_current_valid_user),
):
    return await CommentDao.remove_vote(comment_id, user)


@router.get("/comments/by_post/{post_id}")
async def comments_by_post(
    post_id: int,
    user: User = Depends(get_current_user_or_none),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    async with async_session_maker() as session:
        # 1. Выбираем все комментарии для данного поста (независимо от уровня вложенности)
        query = (
            select(Comment)
            .filter(Comment.post_id == post_id)
            .order_by(Comment.created_at.desc())
        )
        result = await session.execute(query)
        all_comments = result.scalars().all()

    # Если комментариев нет, возвращаем пустой список
    if not all_comments:
        return []

    # 2. Преобразуем каждый комментарий в словарь и добавляем ключ "children", в который будем вкладывать дочерние комментарии
    comment_dict = {}
    for comment in all_comments:
        # Используем метод to_dict без автодобавления дочерних (мы собираем дерево самостоятельно)
        data = comment.to_dict(include_replies=False)
        data["children"] = []
        comment_dict[comment.id] = data

    # 3. Построение дерева: собираем корневые комментарии и вставляем дочерние в поле "children"
    root_comments = []
    for comment in all_comments:
        if comment.parent_comment_id is None:
            # Корневой комментарий
            root_comments.append(comment_dict[comment.id])
        else:
            parent = comment_dict.get(comment.parent_comment_id)
            if parent:
                parent["children"].append(comment_dict[comment.id])
            else:
                # Если родитель не найден – можно залогировать эту ситуацию
                print(
                    f"Не найден родительский комментарий для comment_id {comment.id}: parent_comment_id {comment.parent_comment_id}"
                )

    # 4. Применяем пагинацию к корневым комментариям (если нужно)
    paginated_root_comments = root_comments[offset : offset + limit]

    # 5. Получаем информацию о голосах, если пользователь есть
    all_ids = [data["id"] for data in comment_dict.values()]
    votes_map = {}
    if user and all_ids:
        user_votes = await VoteDao.get_user_votes_for_comments(user.id, all_ids)
        votes_map = {vote.comment_id: vote.is_upvote for vote in user_votes}

    # Рекурсивная функция, чтобы пройтись по всем уровням и добавить данные голосов
    def assign_votes(comment_item):
        comment_item["user_vote"] = votes_map.get(comment_item["id"], None)
        for child in comment_item["children"]:
            assign_votes(child)

    for comment in paginated_root_comments:
        assign_votes(comment)

    # 6. Возвращаем дерево корневых комментариев с вложенными дочерними
    return paginated_root_comments


@router.get("/{comment_id}")
async def get_comment_by_id(comment_id: int):
    comment = await CommentDao.find_one_or_none_by_id(comment_id)
    if not comment:
        return {"detail": "Post not found"}
    post = await PostDao.find_one_or_none_by_id(comment.post_id)
    comment = comment.to_dict()
    comment["post_title"] = post.title
    return comment
