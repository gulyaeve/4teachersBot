FROM python:3.10.2-slim-bullseye

WORKDIR /src

COPY requirements.txt /src
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . /src
RUN mkdir /src/logs