from pydantic import BaseModel, Field


class SubRedditSchema(BaseModel):
    id: int
    name: str = Field(..., min_length=1, max_length=25)
    description: str = Field(None, max_length=255)


class SubRedditCreateSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=25)
    description: str = Field(None, max_length=255)


class SubRedditFindSchema(BaseModel):
    name: str = Field(None, min_length=1, max_length=25)


class SubRedditDeleteSchema(BaseModel):
    id: int


class PostCreateSchema(BaseModel):
    subreddit_id: int
    title: str = Field(...,  min_length=1, max_length=300)
    content: str = Field(None, max_length=40000)


class CommentCreateSchema(BaseModel):
    post_id: int
    content: str
