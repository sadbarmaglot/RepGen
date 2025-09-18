FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install uv

RUN uv pip install --system --no-cache-dir -r requirements.txt