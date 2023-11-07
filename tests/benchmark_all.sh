#!/bin/bash

VERSION=$(cat sscape/version.txt)
BRANCH=$(git branch --show-current 2>/dev/null)

HOSTNAME=$(hostname)
OUTPUT_DIR=sscape_benchmarking/report/data/

# Create host desc file:
sscape_benchmarking/tests/benchmark_host.sh ${OUTPUT_DIR}

## Inference test:
# Pre-requisite: Download the models:
make -C docker/ MODELS=all install-models
# Run inference test:
mkdir -p ${OUTPUT_DIR}/${HOSTNAME}
docker/scenescape-start sscape_benchmarking/tests/benchmark_inference.sh ${OUTPUT_DIR}/${HOSTNAME}

# Run scene test:
# sscape_benchmarking/tests/benchmark_scene.sh

pushd sscape_benchmarking
postproc/run.sh ${HOSTNAME} ${VERSION}_${BRANCH}
popd
