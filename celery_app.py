import requests
from bs4 import BeautifulSoup
from celery import Celery
import time
from celery.exceptions import SoftTimeLimitExceeded
import celery.states as states
import random

redis_url = f"redis://:olezha@localhost:6379/0"

app = Celery('app', broker=redis_url, backend=redis_url)


@app.task
def hello() -> str:
    print('Hello Celery!')
    return 'Hello World!'

@app.task
def sleepy_hello() -> str:
    import time
    time.sleep(5)
    print('Hello Celery!')
    return 'Hello World!'

@app.task
def addition(x: int, y: int) -> int:
    return x + y

@app.task(bind=True, max_retries=10)
def random_error(self) -> str:
    import random
    try:
        if random.randint(1, 20) > 10:
            print(1/0)
    except ZeroDivisionError as ex:
        self.retry(exc=ex, countdown=3)
    print(1)
    return 'Ура наконец-то выполнилось'

@app.task(bind=True, max_retries=3)
def generate_error(self):
    try:
        raise RuntimeError
    except RuntimeError:
        self.retry(countdown=1)

@app.task(bind=True)
def long_task(self):
    import time
    for i in range(5):
        # что-то делает
        time.sleep(2)
        self.update_state(state='PROGRESS', meta={"data": f"process {i} done"})

@app.task(bind=True)
def complex_task(self, iterations):
    total_iterations = iterations
    for i in range(1, iterations + 1):
        time.sleep(random.uniform(0.1, 1))
        self.update_state(
            state="PROGRES",
            meta={
                'current': i,
                'progress': int((i / total_iterations) * 100),
            }
        )
        if random.random() < 0.3: # Симуляция непредвиденной ошибки
            try:
                print(1 / 0)
            except ZeroDivisionError:
                self.update_state(
                    state=states.FAILURE,
                    meta={
                        'current': i,
                        'total': total_iterations,
                        'error': "ZeroDivisionError: division by zero",
                        'message': f"Failed at iteration {i}."
                    }
                )
    return {"status": "success", "iterations": iterations}

@app.task(bind=True, time_limit=10, soft_time_limit=5)
def time_limit_task(self):
    try:
        time.sleep(6)
    except SoftTimeLimitExceeded:
        print("АААА ЧТО-ТО НЕ ТАК ПОМОГИТЕ СПАСИТЕ")
        self.update_state(state="LONG_PROGRES", meta={"detail": "таска выполняется слишком долго"})
        time.sleep(6)


@app.task(name="some_task", queue="some_queue")
def some_task():
    ...

@app.task(rate_limit='1/s')
def high_load_task():
    ...


@app.task(bind=True, time_limit=120)
def parse_repositories(self, username: str):
    try:
        url = f"https://github.com/{username}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        repositories = soup.find_all("li", class_="repo-list-item")
        self.update_state(state="PROGRES", meta={"detail": "спарсили репо"})
        repo_list = []
        for repository in repositories:
            repo_list.append(repository.find("a").text)
            self.update_state(state="PROGRES", meta={"detail": f'добавили {repository.find("a").text} в список'})

        import json
        with open("repositories.json", "w", encoding="utf-8") as file:
            json.dump({username: repo_list}, file, indent=4, ensure_ascii=False)
        self.update_state(state="PROGRES", meta={"detail": f'добавили данные в файл'})
    except Exception as e:
        self.retry(exc=e, countdown=3)