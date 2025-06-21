FROM python:3.14-rc-alpine3.21

WORKDIR /app

COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt

COPY . .

RUN ["python3", "main.py"]