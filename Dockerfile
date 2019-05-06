FROM python:3.7.3-alpine3.9

ADD . /app
WORKDIR /app

EXPOSE 3344
RUN pip install -r requirements.txt
ENTRYPOINT python main.py