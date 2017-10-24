# PaddlePaddle.org Install Guide

## Run from Docker

##### Clone repo
```
git clone https://github.com/PaddlePaddle/PaddlePaddle.org.git
```

##### Building Image

```
cd <project-dir>
docker build -t paddlepaddle.org .
```

##### Run Docker Image
**Note:**  Please contact product team (Varun, Jeff, Daming, Thuan) for the external_template_dir

###### Create portal.env file with the following variables

```
ENV=development
SECRET_KEY="my_secret_key"
```

###### Run Docker Image
```
docker run -d -p 8000:8000 --env-file portal.env -v <content_dir>:/var/content paddlepaddle.org:latest
```

## Local Development

##### Clone repo
```
git clone https://github.com/PaddlePaddle/PaddlePaddle.org.git
```

##### Install compass
```
gem update --system
gem install compass
```

##### Setup virtual environment and install requirements
```
cd paddlepaddle-portal/portal
virtualenv venv
```

##### Add environment variables in venv/bin/activate
```
export ENV="development"
export SECRET_KEY="my_secret_key"
export CONTENT_DIR="<dir where content dir reside>"
```

##### Source virtualenv
```
source venv/bin/activate
```

##### Install requirements

###### Install gettext
```
[macOS]: brew install gettext
[Ubuntu]: apt-get install gettext
```

```
pip install -r requirements.txt
```

#### Build localization files

```
python manage.py compilemessages -l zh
```

##### Startup server
```
python manage.py runserver
```

##### Open up another terminal and run compass (to rebuild css files)
```
cd <project-dir>/portal
compass watch ./static/
```

