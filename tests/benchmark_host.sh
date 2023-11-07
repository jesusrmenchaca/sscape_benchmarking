#!/bin/bash

TARGETDIR=$1

function get_host_cpufreq()
{
  MHZ=$( lscpu | grep 'CPU MHz' )
  if [[ -z "${MHZ}" ]]
  then
    GHZ=$( lscpu | grep 'GHz' | sed 's/.* \([0-9\.]\+\)GHz.*/\1/g' )
    if [[ -n "${GHZ}" ]]
    then
      MHZ=$( echo "${GHZ}" | awk '{ printf("%d", $1 * 1000) }' )
    fi
  fi
  echo $MHZ
}


function get_host_gpus()
{
  NGPUS=$(ls -l /dev/dri/render* | wc -l)
  echo $NGPUS
}

HOSTNAME=$(hostname)
FREQ=$(get_host_cpufreq)
BOGO=$(lscpu | grep -i bogo | awk '{print $2}')
NGPUS=$(get_host_gpus)

TARGETFILE=${TARGETDIR}/desc_${HOSTNAME}.csv
echo "Saving into ${TARGETFILE}"
echo "NAME,CORES,FREQ,GPU,BOGOMIPS" > ${TARGETFILE}
echo "${HOSTNAME}, $(nproc), ${FREQ}, ${NGPUS},${BOGO}" >> ${TARGETFILE}
