FROM python:3.14-rc-alpine

WORKDIR /app

RUN apk add --no-cache build-base

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN ["python3", "main.py"]
