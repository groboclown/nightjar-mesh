#!/bin/bash

mkdir /tmp/${TESTFILE}
mkdir /tmp/${TESTFILE}/bin

cp ${SRC_DIR}/restart-envoy.sh /tmp/${TESTFILE}/.
cp ${TEST_DIR}/mock-script1.sh /tmp/${TESTFILE}/bin/envoy
cp /bin/kill /bin/original-kill
cp ${TEST_DIR}/mock-script2.sh /bin/kill
chmod +x /tmp/${TESTFILE}/bin/envoy /bin/kill
export PATH="/tmp/${TESTFILE}/bin:${PATH}"

cd /tmp/${TESTFILE}

# TEST 1 - Envoy not already running.
export SUCCESS_FILE1=/tmp/${TESTFILE}/1-ran1.txt
export ARGS_FILE1=/tmp/${TESTFILE}/1-args1.txt
export PID_FILE1=/tmp/${TESTFILE}/1-pid1.txt
test -f "${SUCCESS_FILE1}" && rm "${SUCCESS_FILE1}"
test -f "${ARGS_FILE1}" && rm "${ARGS_FILE1}"
test -f "${PID_FILE1}" && rm "${PID_FILE1}"
export MOCK_EXIT_CODE1=0
export SUCCESS_FILE2=/tmp/${TESTFILE}/1-ran2.txt
export ARGS_FILE2=/tmp/${TESTFILE}/1-args2.txt
export PID_FILE2=/tmp/${TESTFILE}/1-pid2.txt
test -f "${SUCCESS_FILE2}" && rm "${SUCCESS_FILE2}"
test -f "${ARGS_FILE2}" && rm "${ARGS_FILE2}"
test -f "${PID_FILE2}" && rm "${PID_FILE2}"
export MOCK_EXIT_CODE2=0
test -f /tmp/envoy.pid && rm /tmp/envoy.pid
/bin/sh /tmp/${TESTFILE}/restart-envoy.sh config-file-name
ec=$?
if [ ${ec} -ne 0 ]; then
  echo "non-zero exit code: ${ec}" >> ${ERROR_DIR}/${TESTFILE}-1.txt
fi
if [ ! -f "${SUCCESS_FILE1}" -o "ran" != "$( cat ${SUCCESS_FILE1} )" ] ; then
  echo "did not run envoy" >> ${ERROR_DIR}/${TESTFILE}-1.txt
fi
if [ ! -f "${ARGS_FILE1}" -o "-c config-file-name" != "$( cat ${ARGS_FILE1} )" ] ; then
  echo "incorrect invocation arguments to envoy" >> ${ERROR_DIR}/${TESTFILE}-1.txt
fi
if [ -f "${SUCCESS_FILE2}" ] ; then
  echo "incorrectly tried to kill envoy" >> ${ERROR_DIR}/${TESTFILE}-1.txt
fi



# TEST 2 - Envoy already running.
export SUCCESS_FILE1=/tmp/${TESTFILE}/2-ran1.txt
export ARGS_FILE1=/tmp/${TESTFILE}/2-args1.txt
export PID_FILE1=/tmp/${TESTFILE}/2-pid1.txt
test -f "${SUCCESS_FILE1}" && rm "${SUCCESS_FILE1}"
test -f "${ARGS_FILE1}" && rm "${ARGS_FILE1}"
test -f "${PID_FILE1}" && rm "${PID_FILE1}"
export MOCK_EXIT_CODE1=0
export SUCCESS_FILE2=/tmp/${TESTFILE}/2-ran2.txt
export ARGS_FILE2=/tmp/${TESTFILE}/2-args2.txt
export PID_FILE2=/tmp/${TESTFILE}/2-pid2.txt
test -f "${SUCCESS_FILE2}" && rm "${SUCCESS_FILE2}"
test -f "${ARGS_FILE2}" && rm "${ARGS_FILE2}"
test -f "${PID_FILE2}" && rm "${PID_FILE2}"
export MOCK_EXIT_CODE2=0
echo "envoy-pid-here" > /tmp/envoy.pid
/bin/sh /tmp/${TESTFILE}/restart-envoy.sh config-file-name
ec=$?
if [ ${ec} -ne 0 ]; then
  echo "non-zero exit code: ${ec}" >> ${ERROR_DIR}/${TESTFILE}-2.txt
fi
if [ ! -f "${SUCCESS_FILE1}" -o "ran" != "$( cat ${SUCCESS_FILE1} )" ] ; then
  echo "did not run envoy" >> ${ERROR_DIR}/${TESTFILE}-2.txt
fi
if [ ! -f "${ARGS_FILE1}" -o "-c config-file-name" != "$( cat ${ARGS_FILE1} )" ] ; then
  echo "incorrect invocation arguments to envoy" >> ${ERROR_DIR}/${TESTFILE}-2.txt
fi
if [ ! -f "${SUCCESS_FILE2}" -o "ran" != "$( cat ${SUCCESS_FILE2} )" ] ; then
  echo "did not run kill command" >> ${ERROR_DIR}/${TESTFILE}-2.txt
fi
if [ ! -f "${ARGS_FILE2}" -o "-term envoy-pid-here" != "$( cat ${ARGS_FILE2} )" ] ; then
  echo "incorrect invocation arguments to kill envoy" >> ${ERROR_DIR}/${TESTFILE}-2.txt
  echo "---------- start [" >> ${ERROR_DIR}/${TESTFILE}-2.txt
  cat ${ARGS_FILE2} >> ${ERROR_DIR}/${TESTFILE}-2.txt
  echo "] end ----------" >> ${ERROR_DIR}/${TESTFILE}-2.txt
fi

# Clean up
cp /bin/original-kill /bin/kill
