from fastapi import FastAPI
from sqladmin import Admin, ModelView

from src.config.database import engine
from src.config.settings import get_db_url
from src.posts.models import Post, Subreddit, Comment, Vote, Subscription
from src.users.models import User
from src.users.router import router as user_routers
from src.posts.router_subreddit import router as subreddit_routers
from src.posts.router_post import router as post_routers
from src.posts.router_comment import router as comment_routers

from src.tasks.hi import welcome

app = FastAPI()

db = get_db_url()


@app.get("/")
async def root():
    welcome.apply_async()
    return {"message": "Hello, World!"}


admin = Admin(app, engine)


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username]


class PostAdmin(ModelView, model=Post):
    column_list = [Post.id, Post.title]


class SubRedditAdmin(ModelView, model=Subreddit):
    column_list = [Subreddit.id, Subreddit.name]


class CommentAdmin(ModelView, model=Comment):
    column_list = [Comment.id, Comment.content]


class VoteAdmin(ModelView, model=Vote):
    column_list = [Vote.id, Vote.is_upvote]


admin.add_view(UserAdmin)
admin.add_view(PostAdmin)
admin.add_view(SubRedditAdmin)
admin.add_view(CommentAdmin)
admin.add_view(VoteAdmin)


app.include_router(user_routers)
app.include_router(subreddit_routers)
app.include_router(comment_routers)
app.include_router(post_routers)

