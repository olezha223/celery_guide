from fastapi import FastAPI
from celery_app import parse_repositories

fast_api_app = FastAPI()

@fast_api_app.get("/get_repositories/{username}")
def get_repositories(username: str) -> str:
    task_id = parse_repositories.delay(username)
    return task_id.id
