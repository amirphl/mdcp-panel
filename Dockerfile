FROM python:3.7
ENV PYTHONUNBUFFERED 1

RUN dpkg-reconfigure -f noninteractive tzdata

RUN apt-get update --fix-missing && \
    apt-get upgrade -y && \
    apt-get -y install tzdata git netcat && \
    ln -sf /usr/share/zoneinfo/UTC /etc/localtime

RUN apt-get update -y
RUN apt-get install software-properties-common -y
RUN apt-get install default-jdk -y
ENV JAVA_HOME /usr/lib/jvm/java-11-openjdk-amd64

RUN pip install coverage
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
RUN apt-get install vim -y

COPY . /code/
