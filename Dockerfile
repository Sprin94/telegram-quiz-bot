FROM python:3.10-slim

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
WORKDIR /app

CMD alembic upgrade head \
    && python ./bot/run.py
