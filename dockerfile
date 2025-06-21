FROM ubuntu/python:3.12-24.04

WORKDIR /app

COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt

COPY . .

RUN ["python3", "main.py"]
