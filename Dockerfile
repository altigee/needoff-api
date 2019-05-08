FROM python:3.7.3-alpine3.9

ADD . /app
WORKDIR /app

EXPOSE 3344
RUN pip install -r requirements.txt

RUN apk update
RUN apk add sqlite sqlite-dev

RUN mkdir /db
RUN /usr/bin/sqlite3 /db/needoff.db

ENTRYPOINT python main.py
