FROM python:3.7
ENV PYTHONUNBUFFERED 1

RUN dpkg-reconfigure -f noninteractive tzdata

RUN apt-get update --fix-missing && \
    apt-get upgrade -y && \
    apt-get -y install tzdata git netcat && \
    ln -sf /usr/share/zoneinfo/UTC /etc/localtime

RUN pip install coverage
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
RUN apt-get install vim -y
COPY . /code/
