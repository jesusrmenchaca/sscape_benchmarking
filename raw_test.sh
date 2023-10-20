#!/bin/bash

MODELS="retail pv0078 pv1016 pv0001 v0002 hpe reid td0001 trresnet pv2000 pv2001 pv2002 v0200 v0201 v0202"

TEST_RESULT=1

FRAMES=5000
PASSING=0
EXPECTED=0

for c in 1 2 4 8 16 32 64 128
do

  for m in ${MODELS}
  do
      echo "Starting test for model ${m} ${c}"
      EXPECTED=$(( $EXPECTED + 1 ))

      TEST_FILE_OUT=omz_model_${m}_out.txt
      TEST_FILE_ERR=omz_model_${m}_err.txt

      if [[ "${m}" == "reid" || "${m}" == "trresnet" ]]
      then
          m="retail+${m}"
      fi

      percebro/rawdetect.py --input sample_data/apriltag-cam1.mp4 --frames ${FRAMES} --model ${m} \
            --preprocess --cores ${c} --max_store_frames 2000 > ${TEST_FILE_OUT} 2> ${TEST_FILE_ERR}
      RESULT=$?
      if [[ $RESULT -ne 0 ]]
      then
          echo "Model ${m} failed!"
          echo "Look at ${TEST_FILE_OUT} / ${TEST_FILE_ERR}"
          break
      else
          MODELFPS=$(tail -n 2 ${TEST_FILE_OUT} | head -n 1 | awk '{print $9}')
          MODELEFF=$(tail -n 1 ${TEST_FILE_OUT} | head -n 1 | awk '{print $5}')
          MODELLAT=$(tail -n 2 ${TEST_FILE_OUT} | head -n 1 | awk '{print $11}')
          echo "Model ${m} --ovcores ${c} gets ${MODELFPS} Ef ${MODELEFF} Latency ${MODELLAT}"
          PASSING=$(( $PASSING + 1 ))

          rm ${TEST_FILE_OUT} ${TEST_FILE_ERR}
      fi
  done

done

if [[ $EXPECTED -eq $PASSING ]]
then
    TEST_RESULT=0
else
    echo "Not all models passed. Expected ${EXPECTED} but only ${PASSING} are passing"
fi

exit $RESULT
