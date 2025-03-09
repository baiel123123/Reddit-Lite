from src.dao.base import BaseDao

from src.users.models import User


class UserDao(BaseDao):
    model = User
