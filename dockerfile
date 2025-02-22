FROM python:3.10.7-buster

WORKDIR /.

ENV TZ="Asia/Kolkata"


COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .


ENTRYPOINT ["python"] 

CMD ["discord_bot.py"]

# CMD [ "python", "manage.py", "runserver"]

# RUN python manage.py runserver
