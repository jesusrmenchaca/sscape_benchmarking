#!/bin/bash

if [[ ! -f ~/.ssh/id_rsa ]]
then
  ssh-keygen -q -N '' -f ~/.ssh/id_rsa
fi

echo "Add the key to github / fmdeviot-ip"
cat ~/.ssh/id_rsa.pub

echo "Then clone the following repo"
git clone git@github.com:jesusrmenchaca/sscape_benchmarking.git

