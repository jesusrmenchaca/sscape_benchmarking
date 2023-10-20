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

#Scene perf test:

tar -xpf ~/jrmencha/dataset/amcrestdb_v14_10-20-2023.tar.bz2

mkdir data
cd data
tar -xpf ~/jrmencha/dataset/amcrest_data.tar.bz2
cd ..

for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14
do

  tests/perf_tests/tc_sail_1871_scene_performance_full --prefix amcrest --datadir data --inputs ${i} > scene_perf_cam_${i}.txt
  tail scene_perf_cam_${i}.txt

done
