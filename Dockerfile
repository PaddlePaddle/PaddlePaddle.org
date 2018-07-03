############################################################
# Dockerfile to run a Django-based web application
# Based on an AMI
# https://medium.com/@rohitkhatana/deploying-django-app-on-aws-ecs-using-docker-gunicorn-nginx-c90834f76e21
############################################################
# Set the base image to use to Ubuntu
FROM ubuntu:16.04

# Set the file maintainer (your name - the file's author)
MAINTAINER Thuan Nguyen

# Update the default application repository sources list
RUN apt-get update && apt-get install -y \
    python-setuptools python-dev build-essential python-pip \
    nginx gettext

# Create application subdirectories
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
