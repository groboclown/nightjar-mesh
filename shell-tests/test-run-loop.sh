#!/bin/bash

mkdir /tmp/${TESTFILE}

cp ${SRC_DIR}/run-loop.sh /tmp/${TESTFILE}/.
cp ${TEST_DIR}/mock-script1.sh /tmp/${TESTFILE}/restart-envoy.sh
cp ${TEST_DIR}/mock-loop-script.sh /tmp/${TESTFILE}/generate-envoy-yaml.sh

cd /tmp/${TESTFILE}

# TEST 1 - Two passes with no changes to the file.
export SUCCESS_FILE1=/tmp/${TESTFILE}/1-ran1.txt
export ARGS_FILE1=/tmp/${TESTFILE}/1-args1.txt
export PID_FILE1=/tmp/${TESTFILE}/1-pid1.txt
test -f "${SUCCESS_FILE1}" && rm "${SUCCESS_FILE1}"
test -f "${ARGS_FILE1}" && rm "${ARGS_FILE1}"
test -f "${PID_FILE1}" && rm "${PID_FILE1}"
export MOCK_EXIT_CODE1=0
export SUCCESS_FILE3=/tmp/${TESTFILE}/1-ran3.txt
export MOCK_DATA3="no-data"
echo "0" > "${SUCCESS_FILE3}"
echo "${MOCK_DATA3}" > /tmp/envoy-config.yaml
export MOCK_EXIT_CODE3=0
export MAX_COUNT=2
export REFRESH_TIME=1
export FAILURE_SLEEP=1
timeout 10 /bin/sh /tmp/${TESTFILE}/run-loop.sh
ec=$?
if [ ${ec} -ne 0 ]; then
  echo "non-zero exit code: ${ec}" >> ${ERROR_DIR}/${TESTFILE}-1.txt
fi
if [ "2" != "$( cat ${SUCCESS_FILE3} )" ]; then
  echo "incorrect loops run: $( cat ${SUCCESS_FILE4} )" >> ${ERROR_DIR}/${TESTFILE}-1.txt
fi
if [ -f /tmp/new-envoy.yaml ]; then
  echo "did not clean up generated file" >> ${ERROR_DIR}/${TESTFILE}-1.txt
fi
