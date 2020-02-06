#!/bin/sh

mkdir /tmp/${TESTFILE}


cp ${SRC_DIR}/generate-envoy-yaml.sh /tmp/${TESTFILE}/.
cp ${TEST_DIR}/mock-generate-data1.py /tmp/${TESTFILE}/generate_template_input_data.py
cp ${TEST_DIR}/mock-generate-data2.py /tmp/${TESTFILE}/generate_envoy_configuration.py


# TEST 1 - invoke the generate script with exit code 0
export SUCCESS_FILE1=/tmp/${TESTFILE}/1-ran1.txt
export ARGS_FILE1=/tmp/${TESTFILE}/1-args1.txt
test -f "${SUCCESS_FILE1}" && rm "${SUCCESS_FILE1}"
test -f "${ARGS_FILE1}" && rm "${ARGS_FILE1}"
export SUCCESS_FILE2=/tmp/${TESTFILE}/1-ran2.txt
export ARGS_FILE2=/tmp/${TESTFILE}/1-args2.txt
test -f "${SUCCESS_FILE2}" && rm "${SUCCESS_FILE2}"
test -f "${ARGS_FILE2}" && rm "${ARGS_FILE2}"
test -f /tmp/input.json && rm /tmp/input.json
export MOCK_EXIT_CODE1=0
export MOCK_EXIT_CODE2=0
export MOCK_DATA1='the-json-data'
export MOCK_DATA2='the-config-data'
cd /tmp/${TESTFILE}
/bin/sh ./generate-envoy-yaml.sh /tmp/${TESTFILE}/1-generated-file.txt
ec=$?
if [ ${ec} -ne 0 ]; then
  echo "non-zero exit code: ${ec}" >> ${ERROR_DIR}/${TESTFILE}-1.txt
fi
if [ ! -f "${SUCCESS_FILE1}" -o "ran" != "$( cat ${SUCCESS_FILE1} )" ] ; then
  echo "did not run generate_template_input_data.py" >> ${ERROR_DIR}/${TESTFILE}-1.txt
fi
if [ ! -f "${ARGS_FILE1}" -o ! -z "$( cat ${ARGS_FILE1} )" ] ; then
  echo "incorrect invocation arguments to generate_template_input_data.py" >> ${ERROR_DIR}/${TESTFILE}-1.txt
  cat ${ARGS_FILE1} >> ${ERROR_DIR}/${TESTFILE}-1.txt
fi
if [ ! -f /tmp/input.json ] ; then
  echo "did not create /tmp/input.json" >> ${ERROR_DIR}/${TESTFILE}-1.txt
fi
if [ -f /tmp/input.json -a "the-json-data" != "$( cat /tmp/input.json )" ] ; then
  echo "incorrect input.json contents:" >> ${ERROR_DIR}/${TESTFILE}-1.txt
  echo "---------- start [" >> ${ERROR_DIR}/${TESTFILE}-1.txt
  cat /tmp/input.json >> ${ERROR_DIR}/${TESTFILE}-1.txt
  echo "] end ----------" >> ${ERROR_DIR}/${TESTFILE}-1.txt
fi
if [ ! -f "${SUCCESS_FILE2}" -o "ran" != "$( cat ${SUCCESS_FILE2} )" ] ; then
  echo "did not run generate_envoy_configuration.py" >> ${ERROR_DIR}/${TESTFILE}-1.txt
fi
if [ ! -f "${ARGS_FILE2}" -o "/tmp/input.json " != "$( cat ${ARGS_FILE2} )" ] ; then
  echo "incorrect invocation arguments to generate_envoy_configuration.py" >> ${ERROR_DIR}/${TESTFILE}-1.txt
  echo "---------- start [" >> ${ERROR_DIR}/${TESTFILE}-1.txt
  cat ${ARGS_FILE2} >> ${ERROR_DIR}/${TESTFILE}-1.txt
  echo "] end ----------" >> ${ERROR_DIR}/${TESTFILE}-1.txt
fi
if [ ! -f /tmp/${TESTFILE}/1-generated-file.txt ] ; then
  echo "did not create /tmp/${TESTFILE}/1-generated-file.txt" >> ${ERROR_DIR}/${TESTFILE}-1.txt
fi
if [ -f /tmp/${TESTFILE}/1-generated-file.txt -a "the-config-data" != "$( cat /tmp/${TESTFILE}/1-generated-file.txt )" ] ; then
  echo "incorrect generated-file contents:" >> ${ERROR_DIR}/${TESTFILE}-1.txt
  echo "---------- start [" >> ${ERROR_DIR}/${TESTFILE}-1.txt
  cat /tmp/${TESTFILE}/1-generated-file.txt >> ${ERROR_DIR}/${TESTFILE}-1.txt
  echo "] end ----------" >> ${ERROR_DIR}/${TESTFILE}-1.txt
fi


# TEST 2 - json output fails
export SUCCESS_FILE1=/tmp/${TESTFILE}/2-ran1.txt
export ARGS_FILE1=/tmp/${TESTFILE}/2-args1.txt
test -f "${SUCCESS_FILE1}" && rm "${SUCCESS_FILE1}"
test -f "${ARGS_FILE1}" && rm "${ARGS_FILE1}"
export SUCCESS_FILE2=/tmp/${TESTFILE}/2-ran2.txt
export ARGS_FILE2=/tmp/${TESTFILE}/2-args2.txt
test -f "${SUCCESS_FILE2}" && rm "${SUCCESS_FILE2}"
test -f "${ARGS_FILE2}" && rm "${ARGS_FILE2}"
test -f /tmp/input.json && rm /tmp/input.json
export MOCK_EXIT_CODE1=12
export MOCK_EXIT_CODE2=0
export MOCK_DATA1='the-json-data'
export MOCK_DATA2='the-config-data'
cd /tmp/${TESTFILE}
/bin/sh ./generate-envoy-yaml.sh /tmp/${TESTFILE}/2-generated-file.txt
ec=$?
if [ ${ec} -ne 1 ]; then
  echo "incorrect exit code: ${ec}" >> ${ERROR_DIR}/${TESTFILE}-2.txt
fi
if [ ! -f "${SUCCESS_FILE1}" -o "ran" != "$( cat ${SUCCESS_FILE1} )" ] ; then
  echo "did not run generate_template_input_data.py" >> ${ERROR_DIR}/${TESTFILE}-2.txt
fi
if [ ! -f "${ARGS_FILE1}" -o ! -z "$( cat ${ARGS_FILE1} )" ] ; then
  echo "incorrect invocation arguments to generate_template_input_data.py" >> ${ERROR_DIR}/${TESTFILE}-2.txt
  cat ${ARGS_FILE1} >> ${ERROR_DIR}/${TESTFILE}-21.txt
fi
if [ -f "${SUCCESS_FILE2}" ] ; then
  echo "incorrectly ran generate_envoy_configuration.py" >> ${ERROR_DIR}/${TESTFILE}-2.txt
fi


# TEST 3 - the config generation fails
export SUCCESS_FILE1=/tmp/${TESTFILE}/3-ran1.txt
export ARGS_FILE1=/tmp/${TESTFILE}/3-args1.txt
test -f "${SUCCESS_FILE1}" && rm "${SUCCESS_FILE1}"
test -f "${ARGS_FILE1}" && rm "${ARGS_FILE1}"
export SUCCESS_FILE2=/tmp/${TESTFILE}/3-ran2.txt
export ARGS_FILE2=/tmp/${TESTFILE}/3-args2.txt
test -f "${SUCCESS_FILE2}" && rm "${SUCCESS_FILE2}"
test -f "${ARGS_FILE2}" && rm "${ARGS_FILE2}"
test -f /tmp/input.json && rm /tmp/input.json
export MOCK_EXIT_CODE1=0
export MOCK_EXIT_CODE2=12
export MOCK_DATA1='the-json-data'
export MOCK_DATA2='the-config-data'
cd /tmp/${TESTFILE}
/bin/sh ./generate-envoy-yaml.sh /tmp/${TESTFILE}/generated-file.txt
ec=$?
if [ ${ec} -ne 1 ]; then
  echo "incorrect exit code: ${ec}" >> ${ERROR_DIR}/${TESTFILE}-3.txt
fi
if [ ! -f "${SUCCESS_FILE1}" -o "ran" != "$( cat ${SUCCESS_FILE1} )" ] ; then
  echo "did not run generate_template_input_data.py" >> ${ERROR_DIR}/${TESTFILE}-3.txt
fi
if [ ! -f "${ARGS_FILE1}" -o ! -z "$( cat ${ARGS_FILE1} )" ] ; then
  echo "incorrect invocation arguments to generate_template_input_data.py" >> ${ERROR_DIR}/${TESTFILE}-3.txt
  cat ${ARGS_FILE1} >> ${ERROR_DIR}/${TESTFILE}-1.txt
fi
if [ ! -f /tmp/input.json ] ; then
  echo "did not create /tmp/input.json" >> ${ERROR_DIR}/${TESTFILE}-3.txt
fi
if [ -f /tmp/input.json -a "the-json-data" != "$( cat /tmp/input.json )" ] ; then
  echo "incorrect input.json contents:" >> ${ERROR_DIR}/${TESTFILE}-3.txt
  echo "---------- start [" >> ${ERROR_DIR}/${TESTFILE}-3.txt
  cat /tmp/input.json >> ${ERROR_DIR}/${TESTFILE}-3.txt
  echo "] end ----------" >> ${ERROR_DIR}/${TESTFILE}-3.txt
fi
if [ ! -f "${SUCCESS_FILE2}" -o "ran" != "$( cat ${SUCCESS_FILE2} )" ] ; then
  echo "did not run generate_envoy_configuration.py" >> ${ERROR_DIR}/${TESTFILE}-3.txt
fi
if [ ! -f "${ARGS_FILE2}" -o "/tmp/input.json " != "$( cat ${ARGS_FILE2} )" ] ; then
  echo "incorrect invocation arguments to generate_envoy_configuration.py" >> ${ERROR_DIR}/${TESTFILE}-3.txt
  echo "---------- start [" >> ${ERROR_DIR}/${TESTFILE}-3.txt
  cat ${ARGS_FILE2} >> ${ERROR_DIR}/${TESTFILE}-3.txt
  echo "] end ----------" >> ${ERROR_DIR}/${TESTFILE}-3.txt
fi
