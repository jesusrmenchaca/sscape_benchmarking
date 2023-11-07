#!/bin/bash

RELEASE=$1
HOSTNAME=$(hostname)

##Scene perf test:
# Find dataset
# If exists, decompress and run test.

pushd ../
FILEDB=$(ls dataset/amcrestdb_*bz2)
FILEDATA=$( ls dataset/amcrest_data*bz2)

if [[ -f ${FILEDB} && -f ${FILEDATA} ]]
then

  tar -xpf dataset/${FILEDB}
  mkdir data
  cd data
  tar -xpf ../dataset/${FILEDATA}
  for ((i=1; i<10;i++)); do mv amcrest0${i}.json amcrest${i}.json; done
  cd ..

  export DBROOT=/workspace
  export SUPASS=admin123
  CAMERA_TEST="1 2 3 4 5 6 7 8 9 10 11 12 13 14"
  for i in $CAMERA_TEST
  do

    tests/perf_tests/tc_sail_1871_scene_performance_full --prefix amcrest --datadir data --inputs ${i} --rate 10 > scene_perf_cam_${i}_${HOSTNAME}.txt

  done

  # Post-process the results 
  

fi

popd
