# Copyright 2013 Thatcher Peskens
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ubuntu:14.04

maintainer Dockerfiles

run apt-get update
run apt-get install -y build-essential git imagemagick
run apt-get install -y python python-dev python-setuptools
run apt-get install -y nginx supervisor
run apt-get install -y python-mysqldb
run apt-get install -y libpq-dev
run easy_install pip

# install uwsgi now because it takes a little while
run pip install uwsgi
add app/requirements.txt /requirements.txt
run pip install -r /requirements.txt

run apt-get install -y software-properties-common python-software-properties
run apt-get update
run add-apt-repository -y ppa:nginx/stable

# install our code
add . /home/server/src

# setup all the configfiles
run echo "daemon off;" >> /etc/nginx/nginx.conf
run rm /etc/nginx/sites-enabled/default
run ln -s /home/server/src/config/nginx-app.conf /etc/nginx/sites-enabled/
run ln -s /home/server/src/config/supervisor-app.conf /etc/supervisor/conf.d/

run mkdir -p /home/jacob/workspace/cnn-text-classification-tf/runs
run cp -r /home/server/src/app/cnn/runs/* /home/jacob/workspace/cnn-text-classification-tf/runs/

expose 80
cmd ["supervisord", "-n"]
