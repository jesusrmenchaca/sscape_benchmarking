#!/bin/bash


VERSION=$1
if [[ -z "$VERSION" ]]
then
  echo "Need to provide a version for this report."
  exit 1
fi
docker run --workdir /workspace -v ${PWD}/:/workspace -it benchmark:latest postproc/run_report.sh $VERSION
