import random

import math
from datetime import datetime


def generate_verification_code():
    return str(random.randint(100000, 999999))


def hot_score(upvotes: int, created_at: datetime) -> float:
    order = math.log(max(upvotes, 1), 10)
    seconds = (created_at - datetime(1970, 1, 1)).total_seconds()
    return round(order + seconds / 45000, 7)