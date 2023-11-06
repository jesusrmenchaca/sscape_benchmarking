#!/bin/bash

VERSION=$1
set -e
mkdir -p report
pushd report

../postproc/gen_report.py --host sail3 --outdir ./ --datadir data --version $VERSION

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

pdflatex report.tex > /dev/null
# Need to run latex TWICE to get references working.
pdflatex report.tex > /dev/null

popd
