#!/bin/bash

OUTDIR=$1
OUTFILE=${OUTDIR}/results_inference.csv

FRAMES=5000
FRAMES=30
ALL_MODELS="retail pv0078 pv1016"
ALL_CORES="2 4 8 12 16"

RESOLUTIONS=()
ALL_INPUTS_JPG="tests/perf_tests/input/20.JPG "
ALL_INPUTS_VGA="sample_data/apriltag-cam1.mp4 "
ALL_INPUTS_720p="sample_data/qcam1.mp4 sample_data/qcam2.mp4 dataset/720p/simple1/Cam1.mp4 dataset/720p/View5/Cam1.mp4"
ALL_INPUTS_HD="dataset/HD/reviewHD/Cam0.mp4 dataset/HD/reviewHD/Cam1.mp4 dataset/HD/reviewHD/Cam2.mp4"

for i in ${ALL_INPUTS_JPG}
do
  RESOLUTIONS+=("720p")
done
for i in ${ALL_INPUTS_VGA}
do
  RESOLUTIONS+=("480p")
done
for i in ${ALL_INPUTS_720p}
do
  RESOLUTIONS+=("720p")
done
for i in ${ALL_INPUTS_HD}
do
  RESOLUTIONS+=("1080p")
done
ALL_INPUTS="${ALL_INPUTS_JPG} ${ALL_INPUTS_VGA} ${ALL_INPUTS_720p} ${ALL_INPUTS_HD}"

echo "INPUT, RES, MODEL, NUM_CORES, DEVICE, LATENCY, FPS" > ${OUTFILE}

DEVICES="CPU"

NGPUS=$(ls /dev/dri/render* 2>/dev/null | wc -l)
for ((i=128; i<128+${NGPUS}; i++))
do
  GPUID=$(( $i - 128 ))
  DEVICES="${DEVICES} GPU.${GPUID}"
done

echo "Starting"
CMD="percebro/percebro --debug --faketime --preprocess --stats --frames ${FRAMES} --intrinsics={\"fov\":70}"

TEST_OUT=bench_perf_out.txt
TEST_ERR=bench_perf_err.txt

INPUT_ID=0
for i in ${ALL_INPUTS}
do

  if [[ -f ${i} ]]
  then

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
          ${CMD} -i ${i} -m ${MODEL} --ovcores ${c} 1> ${TEST_OUT} 2> ${TEST_ERR}

          if [[ $? -ne 0 ]]
          then
            echo "Benchmarking aborted on ${i}/${c}/${m}/${d}"
            echo "Check ${TEST_OUT}/${TEST_ERR} files"
            exit 1
          fi
          FPS=$(tail -n 3 ${TEST_ERR} | head -n 1 | awk '{print $2}')
          LATENCY=$(tail -n 3 ${TEST_ERR} | head -n 1 | awk '{print $3}')

          echo "${i}, ${RESOLUTIONS[$INPUT_ID]}, ${m}, ${c}, ${d}, ${LATENCY}, ${FPS}" >> ${OUTFILE}
          echo "$i on $c cores on dev $d got ${FPS} fps, ${LATENCY} ms latency"
          break
        done

      done

    done
  fi

  INPUT_ID=$(( $INPUT_ID + 1 ))
  echo "INPUT_ID: ${INPUT_ID}"
  if [[ ${INPUT_ID} -gt 2 ]]
  then
    break
  fi
done

rm -f ${TEST_OUT} ${TEST_ERR}

