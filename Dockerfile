FROM python:3.12

WORKDIR /app

ADD bot.py .

COPY requirements.txt ./
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python", "-u", "./bot.py" ]
