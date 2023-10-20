#!/bin/bash

cd ~/jrmencha/builds/
cd intel-proxy-setup
sudo apt --reinstall install network-manager
sudo ./setup.sh
cd ..
cd app*
cd docker
sudo ./get_docker.sh
#Log out.
cd ../../
sudo mkdir -p /etc/init && touch /etc/init/docker.conf
cd intel-proxy-setup
sudo ./setup.sh

sudo apt-get install -y bzip2
cd ../app*
screen -S scenescape-dev
export http_proxy=http://10.7.211.16:911
export https_proxy=http://10.7.211.16:912

export SUPASS=thisissupass
export CERTPASS=thisiscert
./deploy.sh

docker-compose down

