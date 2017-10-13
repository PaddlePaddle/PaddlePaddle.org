#!/bin/bash
set -e

# deploy to remote server
openssl aes-256-cbc -d -a -in ubuntu.pem.enc -out ubuntu.pem -k $DEC_PASSWD


eval "$(ssh-agent -s)"
chmod 400 ubuntu.pem

ssh-add ubuntu.pem

rsync -r /Users/ludaming/Baidu_USA_DamingLu/externalTemplates2/ ubuntu@52.76.173.135:/var/content_staging/

chmod 644 ubuntu.pem

rm ubuntu.pem
