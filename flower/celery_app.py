import requests
from bs4 import BeautifulSoup
from celery import Celery

redis_url = f"redis://:olezha@localhost:6379/0"

app = Celery('app', broker=redis_url, backend=redis_url)


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