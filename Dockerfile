############################################################
# Dockerfile to run a Django-based web application
# Based on an AMI
# https://medium.com/@rohitkhatana/deploying-django-app-on-aws-ecs-using-docker-gunicorn-nginx-c90834f76e21
############################################################
# Set the base image to use to Ubuntu
FROM ubuntu:16.04

# Set the file maintainer (your name - the file's author)
MAINTAINER Thuan Nguyen

ARG CONTENT_DIR_ARG=/var/content
ENV CONTENT_DIR=$CONTENT_DIR_ARG

# Update the default application repository sources list
RUN apt-get update && apt-get -y upgrade && \
    apt-get install -y python python-pip \
    python-dev \
    cmake \
    golang-go \
    git \
    nginx \
    gettext \
    build-essential \
    python-wheel \
    libboost-dev \
    swig

# Create application subdirectories
WORKDIR $CONTENT_DIR_ARG
WORKDIR /var/www
COPY . .

# Port to expose
EXPOSE 8000

WORKDIR /var/www/portal
RUN pip install -r requirements.txt

COPY ./docker-entrypoint.sh .
COPY ./django_nginx.conf /etc/nginx/sites-available/
RUN ln -s /etc/nginx/sites-available/django_nginx.conf /etc/nginx/sites-enabled
RUN echo "daemon off;" >> /etc/nginx/nginx.conf
ENTRYPOINT ["./docker-entrypoint.sh"]