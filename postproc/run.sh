#!/bin/bash

HOST=$1
VERSION=$2
if [[ -z "${VERSION}" || -z "${HOST}" ]]
then
  echo "Need to provide a host + version for this report."
  exit 1
fi
docker run --workdir /workspace -v ${PWD}/:/workspace -it benchmark:latest postproc/run_report.sh ${HOST} ${VERSION}
