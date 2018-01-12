FROM python:3.6

RUN pip install python-binance slackClient
COPY . /

ENTRYPOINT ["python", "bot.py"]