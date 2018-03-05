############################################################
# Dockerfile to run a Django-based web application
# Based on an AMI
# https://medium.com/@rohitkhatana/deploying-django-app-on-aws-ecs-using-docker-gunicorn-nginx-c90834f76e21
############################################################
# Set the base image to use to Ubuntu
FROM paddlepaddle/paddle:latest-dev

# Set the file maintainer (your name - the file's author)
MAINTAINER Thuan Nguyen

ARG CONTENT_DIR_ARG=/var/content
ENV CONTENT_DIR=$CONTENT_DIR_ARG

ARG UBUNTU_MIRROR
RUN /bin/bash -c 'if [[ -n ${UBUNTU_MIRROR} ]]; then sed -i 's#http://archive.ubuntu.com/ubuntu#${UBUNTU_MIRROR}#g' /etc/apt/sources.list; fi'

# Update the default application repository sources list
RUN apt-get update && apt-get install -y \
    nginx \
    gettext

ENV GOROOT=/usr/local/go GOPATH=/root/gopath
# should not be in the same line with GOROOT definition, otherwise docker build could not find GOROOT.
ENV PATH=${PATH}:${GOROOT}/bin:${GOPATH}/bin

# Create application subdirectories
WORKDIR $CONTENT_DIR_ARG
WORKDIR /var/www
COPY . .

# Port to expose
EXPOSE 8000

WORKDIR /var/www/portal
RUN pip uninstall -y numpy
RUN pip install -r requirements.txt

COPY ./docker-entrypoint.sh .
COPY ./django_nginx.conf /etc/nginx/sites-available/
RUN ln -s /etc/nginx/sites-available/django_nginx.conf /etc/nginx/sites-enabled
RUN echo "daemon off;" >> /etc/nginx/nginx.conf
ENTRYPOINT ["./docker-entrypoint.sh"]
