#!/bin/bash

FRAMES=5000
ALL_MODELS="retail pv0078 pv1016"
ALL_CORES="2 4 8 12 16"


ALL_INPUTS_JPG="tests/perf_tests/input/20.JPG "
ALL_INPUTS_VGA="sample_data/apriltag-cam1.mp4 "
ALL_INPUTS_720p="sample_data/qcam1.mp4 sample_data/qcam2.mp4 dataset/720p/simple1/Cam1.mp4 dataset/720p/View5/Cam1.mp4"
ALL_INPUTS_HD="dataset/HD/reviewHD/Cam0.mp4 dataset/HD/reviewHD/Cam1.mp4 dataset/HD/reviewHD/Cam2.mp4"

ALL_INPUTS="${ALL_INPUTS_JPG} ${ALL_INPUTS_VGA} ${ALL_INPUTS_720p} ${ALL_INPUTS_HD}"

echo "INPUT, MODEL, NUM_CORES, DEVICE, LATENCY, FPS" > results.csv

GPUS=$(ls /dev/dri/render*)
DEVICES="CPU"
if [[ -e /dev/dri/render128 ]]
then
  DEVICES="${DEVICES} GPU.0"
fi
if [[ -e /dev/dri/render128 ]]
then
  DEVICES="${DEVICES} GPU.1"
fi

echo "Starting"

for i in ${ALL_INPUTS}
do

  for c in ${ALL_CORES}
  do

    for m in ${ALL_MODELS}
    do

      for d in ${DEVICES}
      do
        MODEL=${m}
        if [[ "$d" != "CPU" ]]
        then
          MODEL="${m}=${d}"
        fi
        echo "Running $i on $c cores on dev $d"
        percebro/percebro --debug --preprocess --stats --frames ${FRAMES} -i ${i} -m ${MODEL} --ovcores ${c} 1> perf_res.txt 2>fps_err.txt
        FPS=$(tail -n 3 fps_err.txt | head -n 1 | awk '{print $2}')
        LATENCY=$(tail -n 3 fps_err.txt | head -n 1 | awk '{print $3}')
        echo "${i}, ${m}, ${c}, ${d}, ${LATENCY}, ${FPS}" >> results.csv
        echo "$i on $c cores on dev $d got ${FPS} fps, ${LATENCY} ms latency"
      done

    done

  done

done

