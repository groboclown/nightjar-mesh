#!/bin/bash

if [ $UID -ne 0 ]; then
  echo "It doesn't look like you're running this from a Docker container."
  echo "Continuing has a chance to corrupt your system.  So this is quitting early."
  echo "==========================================="
  echo "Total: 1 Failed"
  exit 1
fi

export ROOT_DIR=$( dirname $0 )
export SRC_DIR="${ROOT_DIR}/nightjar-base/nightjar-src"


for TEST_SUITE in "$@" ; do
  export SUITE_DIR="${ROOT_DIR}/${TEST_SUITE}"
  export TEST_DIR="${ROOT_DIR}/${TEST_SUITE}/shell-tests"
  echo ""
  echo ""
  echo "***********************************************************************"
  echo "Test Suite ${TEST_SUITE}"
  export ERROR_DIR=/tmp/errors/${TEST_SUITE}
  mkdir -p ${ERROR_DIR} || exit 1

  for tf in ${TEST_DIR}/test-*.sh ; do
    echo ""
    echo ""
    echo "Running test ${tf}"
    echo "==========================================="
    export TEST_NAME=$( basename ${tf} .sh )
    export TESTFILE="${TEST_SUITE}-${TEST_NAME}"
    timeout 30 /bin/bash -x "${tf}"

  done
done

echo ""
echo ""
echo "Failed Tests"
echo "============================================================================="
for f in ${ERROR_DIR}/* ; do
  if [ -f "${f}" ]; then
    echo "> $( basename ${f} .txt ):"
    cat ${f}
    echo "----------------------------"
  fi
done
error_count=$( ls -1 ${ERROR_DIR} | wc -l )
echo "============================================================================="
echo "Total: ${error_count} Failed"
exit ${error_count}
