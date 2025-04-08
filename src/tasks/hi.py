from src.celery_app import celery_app


@celery_app.task
def welcome():
    return "Hey yo!"
