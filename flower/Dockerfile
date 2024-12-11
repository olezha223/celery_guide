FROM python:3.10

RUN mkdir "api"

ENV PYTHONDONTWRITEBYCODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt /api/requirements.txt

WORKDIR api

RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "fastapi_app:fast_api_app", "--host", "0.0.0.0", "--port", "8000"]