#!/bin/bash

HOST=$1
VERSION=$2

set -e
mkdir -p report
pushd report

cp ../postproc/logo.svg data/
#../postproc/gen_charts.py --input data/${HOST}/results_${HOST}.csv --outdir data
../postproc/gen_report.py --host ${HOST} --outdir ./ --datadir data --version $VERSION

#pushd data
for m in *svg
do
  NAMEPDF=$(echo $m | sed 's/svg/pdf/g')
  echo "$m -> ${NAMEPDF}"
  inkscape -D $m -o ${NAMEPDF} --export-latex > /dev/null 2>&1
  RESULT=$?
  if [[ $RESULT -ne 0 ]]
  then
    echo "Failed processing ${m}"
  fi
done
#popd

#Uncomment for debugging.
#pdflatex report.tex
pdflatex report.tex > /dev/null
# Need to run latex TWICE to get references working.
pdflatex report.tex > /dev/null

popd
