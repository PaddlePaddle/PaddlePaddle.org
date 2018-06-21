#!/bin/bash
set -e

# deploy to remote server
openssl aes-256-cbc -d -a -in $TRAVIS_BUILD_DIR/scripts/travis/ubuntu.pem.enc -out ubuntu.pem -k $DEC_PASSWD

eval "$(ssh-agent -s)"
chmod 400 ubuntu.pem

ssh-add ubuntu.pem

ssh -i ubuntu.pem ubuntu@$STAGE_DEPLOY_IP << EOF
  set -e

  cd /var/www/portal
  tar -czvf workspace.tar.gz pages/
  aws s3 cp workspace.tar.gz s3://paddlepaddle.org/workspace.tar.gz --grants read=uri=http://acs.amazonaws.com/groups/global/AllUsers

EOF

chmod 644 ubuntu.pem
rm ubuntu.pem
