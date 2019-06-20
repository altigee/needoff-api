FROM python:3.7.3-alpine3.9

ADD . /app
WORKDIR /app

RUN apk update
RUN apk add git sqlite sqlite-dev

EXPOSE 3344
RUN pip install -r requirements.txt

RUN mkdir /db
RUN /usr/bin/sqlite3 /db/needoff.db

ENTRYPOINT python main.py
