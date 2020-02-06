#!/bin/bash

if [ $UID -ne 0 ]; then
  echo "It doesn't look like you're running this from a Docker container."
  echo "Continuing has a chance to corrupt your system.  So this is quitting early."
  echo "==========================================="
  echo "Total: 1 Failed"
  exit 1
fi


export TEST_DIR=$( dirname "$0" )
export ROOT_DIR="${TEST_DIR}/.."
export SRC_DIR="${ROOT_DIR}/nightjar-src"
export ERROR_DIR=/tmp/errors
mkdir -p ${ERROR_DIR}

for tf in ${TEST_DIR}/test-*.sh ; do
  echo ""
  echo ""
  echo "Running test ${tf}"
  echo "==========================================="
  export TESTFILE=$( basename ${tf} .sh )
  timeout 30 /bin/bash ${TEST_DIR}/${TESTFILE}.sh

done

echo ""
echo ""
echo "Failed Tests"
echo "==========================================="
for f in ${ERROR_DIR}/* ; do
  if [ -f "${f}" ]; then
    echo "> $( basename ${f} .txt ):"
    cat ${f}
    echo "----------------------------"
  fi
done
error_count=$( ls -1 ${ERROR_DIR} | wc -l )
echo "==========================================="
echo "Total: ${error_count} Failed"
exit ${error_count}
