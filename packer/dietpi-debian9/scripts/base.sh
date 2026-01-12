#!/bin/bash

pushd ${HOME}
set -x
##
mkdir -p ~/.ssh/
wget https://github.com/alexz-kh.keys -O ~/.ssh/authorized_keys
chmod 0600 ~/.ssh/authorized_keys
echo -e "termcapinfo xterm* ti@:te@ \ndefscrollback 10000\n" >> ~/.screenrc

##
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y ca-certificates sudo wget screen curl locales whiptail ncurses-bin bzip2 acpid cryptsetup zlib1g-dev wget curl make net-tools rsync htop iotop

export PREIMAGE_INFO="http://example.com"
export G_HW_MODEL='35'
export WIFI_REQUIRED=1

export GIT_BRANCH='master'
#export GIT_BRANCH='testing' #DEV only
pushd /tmp/
wget https://raw.githubusercontent.com/Fourdee/DietPi/$GIT_BRANCH/PREP_SYSTEM_FOR_DIETPI.sh -O PREP_SYSTEM_FOR_DIETPI.sh
chmod +x PREP_SYSTEM_FOR_DIETPI.sh
export GIT_BRANCH=$GIT_BRANCH
#./PREP_SYSTEM_FOR_DIETPI.sh

sleep 99h || true
###
sudo mkdir -p /home/dietpi/.ssh/
sudo wget https://github.com/alexz-kh.keys -O /home/dietpi/.ssh/authorized_keys
sudo chmod 0600 /home/dietpi/.ssh/authorized_keys
sudo chmod 700 /home/dietpi/.ssh
sudo chown -R dietpi:dietpi /home/dietpi/.ssh
sudo /bin/bash -c 'echo -e "r00tme\nr00tme"|passwd dietpi'

###
sudo /bin/bash -c 'dd if=/dev/zero of=/EMPTY bs=1M || true'
sudo rm -f /EMPTY
sudo /bin/bash -c 'echo 3 > /proc/sys/vm/drop_caches'
sudo sync
