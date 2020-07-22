#!/bin/bash

mkdir -p /tmp/${TESTFILE}
mkdir -p /tmp/${TESTFILE}/bin

cp ${SUITE_DIR}/envoy-docker/nightjar-src/restart-envoy.sh /tmp/${TESTFILE}/.
cp /bin/kill /bin/original-kill
cp ${TEST_DIR}/mock-script2.sh /bin/kill
cp /usr/local/bin/envoy /usr/local/bin/original-envoy
cp ${TEST_DIR}/mock-script1.sh /usr/local/bin/envoy
chmod +x usr/local/bin/envoy /bin/kill

cd /tmp/${TESTFILE}



# TEST 1 - Have a config file, and envoy not already running.
ERROR_FILE=${ERROR_DIR}/${TESTFILE}-1.txt

# exec file 1: envoy
export SUCCESS_FILE1=/tmp/${TESTFILE}/1-ran1.txt
export ARGS_FILE1=/tmp/${TESTFILE}/1-args1.txt
export PID_FILE1=/tmp/${TESTFILE}/1-pid1.txt
test -f "${SUCCESS_FILE1}" && rm "${SUCCESS_FILE1}"
test -f "${ARGS_FILE1}" && rm "${ARGS_FILE1}"
test -f "${PID_FILE1}" && rm "${PID_FILE1}"
export MOCK_EXIT_CODE1=0

# exec file 2: kill
#  - non-zero exit code, which means envoy is not running.
export SUCCESS_FILE2=/tmp/${TESTFILE}/1-ran2.txt
export ARGS_FILE2=/tmp/${TESTFILE}/1-args2.txt
export PID_FILE2=/tmp/${TESTFILE}/1-pid2.txt
test -f "${SUCCESS_FILE2}" && rm "${SUCCESS_FILE2}"
test -f "${ARGS_FILE2}" && rm "${ARGS_FILE2}"
test -f "${PID_FILE2}" && rm "${PID_FILE2}"
export MOCK_EXIT_CODE2=1

export ENVOY_PID_FILE=/tmp/${TESTFILE}/1-pid.txt
echo "the-envoy-pid" > ${ENVOY_PID_FILE}
touch /tmp/${TESTFILE}/1-config.txt
export ENVOY_LOG_LEVEL=blah
export ENVOY_BASE_ID=foo

/bin/sh /tmp/${TESTFILE}/restart-envoy.sh /tmp/${TESTFILE}/1-config.txt
ec=$?
if [ ${ec} -ne 0 ]; then
  echo "non-zero exit code: ${ec}" >> ${ERROR_FILE}
fi
if [ ! -f "${SUCCESS_FILE2}" -o "ran" != "$( cat ${SUCCESS_FILE2} )" ] ; then
  echo "did not run kill" >> ${ERROR_FILE}
fi
if [ ! -f "${ARGS_FILE2}" -o "-0 the-envoy-pid" != "$( cat ${ARGS_FILE2} )" ] ; then
  echo "incorrect invocation arguments to kill" >> ${ERROR_FILE}
fi
if [ ! -f "${SUCCESS_FILE1}" -o "ran" != "$( cat ${SUCCESS_FILE1} )" ] ; then
  echo "did not run envoy" >> ${ERROR_FILE}
fi
if [ ! -f "${ARGS_FILE1}" -o "--log-level blah -c /tmp/${TESTFILE}/1-config.txt --base-id foo" != "$( cat ${ARGS_FILE1} )" ] ; then
  echo "incorrect invocation arguments to envoy" >> ${ERROR_FILE}
  echo "---------- start [" >> ${ERROR_FILE}
  cat ${ARGS_FILE1} >> ${ERROR_FILE}
  echo "] end ----------" >> ${ERROR_FILE}
fi



# TEST 2 - Have a config file, and envoy already running.
ERROR_FILE=${ERROR_DIR}/${TESTFILE}-2.txt

# exec file 1: envoy
# - should never be run
export SUCCESS_FILE1=/tmp/${TESTFILE}/2-ran1.txt
export ARGS_FILE1=/tmp/${TESTFILE}/2-args1.txt
export PID_FILE1=/tmp/${TESTFILE}/2-pid1.txt
test -f "${SUCCESS_FILE1}" && rm "${SUCCESS_FILE1}"
test -f "${ARGS_FILE1}" && rm "${ARGS_FILE1}"
test -f "${PID_FILE1}" && rm "${PID_FILE1}"
export MOCK_EXIT_CODE1=2

# exec file 2: kill
#  - 0 exit code, which means envoy is running.
export SUCCESS_FILE2=/tmp/${TESTFILE}/1-ran2.txt
export ARGS_FILE2=/tmp/${TESTFILE}/1-args2.txt
export PID_FILE2=/tmp/${TESTFILE}/1-pid2.txt
test -f "${SUCCESS_FILE2}" && rm "${SUCCESS_FILE2}"
test -f "${ARGS_FILE2}" && rm "${ARGS_FILE2}"
test -f "${PID_FILE2}" && rm "${PID_FILE2}"
export MOCK_EXIT_CODE2=0

export ENVOY_PID_FILE=/tmp/${TESTFILE}/1-pid.txt
echo "the-envoy-pid2" > ${ENVOY_PID_FILE}
touch /tmp/${TESTFILE}/2-config.txt
export ENVOY_LOG_LEVEL=blah
export ENVOY_BASE_ID=foo

/bin/sh /tmp/${TESTFILE}/restart-envoy.sh /tmp/${TESTFILE}/2-config.txt
ec=$?
if [ ${ec} -ne 0 ]; then
  echo "non-zero exit code: ${ec}" >> ${ERROR_FILE}
fi
if [ ! -f "${SUCCESS_FILE2}" -o "ran" != "$( cat ${SUCCESS_FILE2} )" ] ; then
  echo "did not run kill" >> ${ERROR_FILE}
fi
if [ ! -f "${ARGS_FILE2}" -o "-0 the-envoy-pid2" != "$( cat ${ARGS_FILE2} )" ] ; then
  echo "incorrect invocation arguments to kill" >> ${ERROR_FILE}
fi
if [ -f "${SUCCESS_FILE1}" ] ; then
  echo "incorrectly ran envoy" >> ${ERROR_FILE}
fi



# TEST 3 - no config file
ERROR_FILE=${ERROR_DIR}/${TESTFILE}-2.txt

# exec file 1: envoy
# - should never be run
export SUCCESS_FILE1=/tmp/${TESTFILE}/2-ran1.txt
export ARGS_FILE1=/tmp/${TESTFILE}/2-args1.txt
export PID_FILE1=/tmp/${TESTFILE}/2-pid1.txt
test -f "${SUCCESS_FILE1}" && rm "${SUCCESS_FILE1}"
test -f "${ARGS_FILE1}" && rm "${ARGS_FILE1}"
test -f "${PID_FILE1}" && rm "${PID_FILE1}"
export MOCK_EXIT_CODE1=2

# exec file 2: kill
#  - should never be run
export SUCCESS_FILE2=/tmp/${TESTFILE}/1-ran2.txt
export ARGS_FILE2=/tmp/${TESTFILE}/1-args2.txt
export PID_FILE2=/tmp/${TESTFILE}/1-pid2.txt
test -f "${SUCCESS_FILE2}" && rm "${SUCCESS_FILE2}"
test -f "${ARGS_FILE2}" && rm "${ARGS_FILE2}"
test -f "${PID_FILE2}" && rm "${PID_FILE2}"
export MOCK_EXIT_CODE2=2

export ENVOY_PID_FILE=/tmp/${TESTFILE}/1-pid.txt
echo "the-envoy-pid3" > ${ENVOY_PID_FILE}
export ENVOY_LOG_LEVEL=blah
export ENVOY_BASE_ID=foo
test -e /tmp/${TESTFILE}/3-config.txt && rm -r /tmp/${TESTFILE}/3-config.txt

/bin/sh /tmp/${TESTFILE}/restart-envoy.sh /tmp/${TESTFILE}/3-config.txt
ec=$?
if [ ${ec} -ne 0 ]; then
  echo "non-zero exit code: ${ec}" >> ${ERROR_FILE}
fi
if [ -f "${SUCCESS_FILE2}" ] ; then
  echo "incorrectly ran kill" >> ${ERROR_FILE}
fi
if [ -f "${SUCCESS_FILE1}" ] ; then
  echo "incorrectly ran envoy" >> ${ERROR_FILE}
fi


# Clean up
mv /bin/original-kill /bin/kill
mv /usr/local/bin/original-envoy /usr/local/bin/envoy
