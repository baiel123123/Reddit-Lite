from typing import Optional

from pydantic import BaseModel, Field


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


class PostCreateSchema(BaseModel):
    subreddit_id: int
    title: str = Field(...,  min_length=1, max_length=300)
    content: str = Field(None, max_length=40000)


class PostFindSchema(BaseModel):
    id: Optional[int] = None
    title: Optional[str] = Field(None, min_length=1, max_length=300)


class PostUpdateSchema(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    content: str = Field(..., max_length=40000)
    subreddit_id: int


class CommentCreateSchema(BaseModel):
    post_id: int
    content: str
