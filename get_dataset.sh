#!/bin/bash

BASEDIR=${PWD}

HOST=fmdeviot-ip
TARGET=${1:-~/jrmencha/builds/applications.ai.scene-intelligence.opensail}
cd ~/jrmencha/
mkdir -p dataset
cd dataset
scp -r jrmencha@${HOST}:~/dataset/* .
cd ${TARGET} && mkdir dataset
cd dataset

for d in city_scene
do

for f in ~/jrmencha/dataset/${d}/*zip
do
  DIR=$(basename ${f} | sed -e 's/\.zip//g')
  mkdir ${DIR} && cd ${DIR}
  unzip ${f}
  cd ..
done

done

cd ${BASEDIR}

cp benchmarking_system.sh ${TARGET}/tests/perf_tests/
pushd ${TARGET}
make -C docker/ install-models MODELS=all

docker/scenescape-start --shell tests/perf_tests/benchmarking_system.sh
