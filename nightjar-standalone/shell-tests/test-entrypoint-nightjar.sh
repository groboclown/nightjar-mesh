#!/bin/bash

# Unlike the other scripts. the entrypoint file has a hard-coded path.
mkdir /nightjar-src
cp ${TEST_DIR}/mock-script1.sh /nightjar-src/run-loop.sh

mkdir /tmp/${TESTFILE}


# TEST 1 - DEBUG_CONTAINER=0
export SUCCESS_FILE1=/tmp/${TESTFILE}/1-ran.txt
export ARGS_FILE1=/tmp/${TESTFILE}/1-args.txt
export PID_FILE1=/tmp/${TESTFILE}/pid
test -f "${SUCCESS_FILE1}" && rm "${SUCCESS_FILE1}"
test -f "${ARGS_FILE1}" && rm "${ARGS_FILE1}"
export MOCK_EXIT_CODE1=0
DEBUG_CONTAINER=0 /bin/sh ${ROOT_DIR}/entrypoint-nightjar.sh
ec=$?
if [ ${ec} -ne 0 ]; then
  echo "non-zero exit code: ${ec}" >> ${ERROR_DIR}/${TESTFILE}-1.txt
fi
if [ ! -f "${SUCCESS_FILE1}" -o "ran" != "$( cat ${SUCCESS_FILE1} )" ] ; then
  echo "did not run loop script" >> ${ERROR_DIR}/${TESTFILE}-1.txt
fi
if [ ! -f "${ARGS_FILE1}" -o ! -z "$( cat ${ARGS_FILE1} )" ] ; then
  echo "incorrect invocation arguments to the run loop script" >> ${ERROR_DIR}/${TESTFILE}-1.txt
fi


# TEST 2 - DEBUG_CONTAINER=1 with arguments
export SUCCESS_FILE1=/tmp/${TESTFILE}/2-ran.txt
export ARGS_FILE1=/tmp/${TESTFILE}/2-args.txt
test -f "${SUCCESS_FILE1}" && rm "${SUCCESS_FILE1}"
test -f "${ARGS_FILE1}" && rm "${ARGS_FILE1}"
export MOCK_EXIT_CODE1=0
DEBUG_CONTAINER=1 /bin/sh ${ROOT_DIR}/entrypoint-nightjar.sh ${TEST_DIR}/mock-script1.sh a b c
ec=$?
if [ ${ec} -ne 0 ]; then
  echo "non-zero exit code: ${ec}" >> ${ERROR_DIR}/${TESTFILE}-2.txt
fi
if [ ! -f "${SUCCESS_FILE1}" -o "ran" != "$( cat ${SUCCESS_FILE1} )" ] ; then
  echo "did not run loop script" >> ${ERROR_DIR}/${TESTFILE}-2.txt
fi
if [ ! -f "${ARGS_FILE1}" -o "a b c" != "$( cat ${ARGS_FILE1} )" ] ; then
  echo "incorrect invocation arguments to the shell invocation" >> ${ERROR_DIR}/${TESTFILE}-2.txt
  echo "---------- start [" >> ${ERROR_DIR}/${TESTFILE}-2.txt
  cat ${ARGS_FILE1} >> ${ERROR_DIR}/${TESTFILE}-2.txt
  echo "] end ----------" >> ${ERROR_DIR}/${TESTFILE}-2.txt
fi


# TEST 3 - exit code from run-loop is exit code of entrypoint.
# Also, all arguments are ignored.
export SUCCESS_FILE1=/tmp/${TESTFILE}/2-ran.txt
export ARGS_FILE1=/tmp/${TESTFILE}/2-args.txt
test -f "${SUCCESS_FILE1}" && rm "${SUCCESS_FILE1}"
test -f "${ARGS_FILE1}" && rm "${ARGS_FILE1}"
export MOCK_EXIT_CODE1=15
DEBUG_CONTAINER=0 /bin/sh ${ROOT_DIR}/entrypoint-nightjar.sh a b c
ec=$?
if [ ${ec} -ne 15 ]; then
  echo "non-zero exit code: ${ec}" >> ${ERROR_DIR}/${TESTFILE}-3.txt
fi
if [ ! -f "${SUCCESS_FILE1}" -o "ran" != "$( cat ${SUCCESS_FILE1} )" ] ; then
  echo "did not run loop script" >> ${ERROR_DIR}/${TESTFILE}-3.txt
fi
if [ ! -f "${ARGS_FILE1}" -o ! -z "$( cat ${ARGS_FILE1} )" ] ; then
  echo "incorrect invocation arguments to the run-loop" >> ${ERROR_DIR}/${TESTFILE}-2.txt
fi
