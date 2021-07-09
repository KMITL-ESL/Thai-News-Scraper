FROM python:3.8.8

RUN apt update -y

RUN apt install -y python3-pip

# EXPOSE 80

COPY . /app

WORKDIR /app

RUN pip3 install -r requirements.txt

CMD python main.py