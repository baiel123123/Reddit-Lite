from datetime import datetime
from typing import Optional

from fastapi import Form
from pydantic import BaseModel, Field, constr


class SubRedditSchema(BaseModel):
    id: int
    name: str = Field(..., min_length=1, max_length=25)
    description: str = Field(None, max_length=255)


class SubRedditCreateSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=25)
    description: str = Field(None, max_length=255)


class SubRedditFindSchema(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=1, max_length=25)


class SubRedditDeleteSchema(BaseModel):
    id: int = Field(..., min_length=1)


class SubRedditUpdateSchema(BaseModel):
    description: str = Field(..., min_length=1, max_length=50)


class PostCreateForm:
    def __init__(
        self,
        subreddit_id: int = Form(...),
        title: constr(min_length=1, max_length=300) = Form(...),
        content: constr(max_length=40000) = Form(None),
    ):
        self.subreddit_id = subreddit_id
        self.title = title
        self.content = content


class PostFindSchema(BaseModel):
    id: Optional[int] = None
    title: Optional[str] = Field(None, min_length=1, max_length=300)


class PostUpdateSchema(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    content: str = Field(..., max_length=40000)
    subreddit_id: int


class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    subreddit_id: Optional[int]
    user_id: int
    upvote: int
    created_at: datetime


class CommentCreateSchema(BaseModel):
    post_id: int
    content: str


class CommentUpdateSchema(BaseModel):
    content: str


class CommentResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    content: str
    created_at: datetime
    upvote: int
    user_vote: Optional[bool] = None


class CommentResponseSchema(BaseModel):
    id: int
    post_id: int
    user_id: Optional[int]
    content: str
    upvote: int
    parent_comment_id: Optional[int]
    created_at: str
    updated_at: str
    user_vote: Optional[bool]

    class Config:
        from_attributes = True
