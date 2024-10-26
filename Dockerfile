FROM python:3.12

ADD bot.py .

RUN pip3 install aiosqlite discord python-dotenv

CMD [ "python", "./bot.py" ]
