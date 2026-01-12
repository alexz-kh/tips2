#!/usr/bin/env bash

set -ex
if [[ ! -d venv ]];then
  virtualenv --python=python3 --system-site-packages --always-copy venv
  source venv/bin/activate
  pip install -U PyYaml gspread oauth2client PyOpenSSL pytz
#  pip install -U https://github.com/nithinmurali/pygsheets/archive/staging.zip
#  pip install --upgrade pyasn1-modules

else
  echo "venv already exist"
fi

exit 
# better to run in docker
apt-get update
apt-get install libapt-pkg-dev python-apt -y


#pip install https://launchpad.net/python-apt/main/0.7.8/+download/python-apt-0.8.5.tar.gz

