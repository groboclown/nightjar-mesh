#!/bin/sh

mkdir /tmp/${TESTFILE}


cp ${SRC_DIR}/generate-envoy-yaml.sh /tmp/${TESTFILE}/.
cp ${TEST_DIR}/mock-generate-data1.py /tmp/${TESTFILE}/generate_template_input_data.py


# TEST 1 - invoke the generate script with exit code 0 and no files to process
ERROR_FILE=${ERROR_DIR}/${TESTFILE}-1.txt
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
export MOCK_DATA1='{"the-json-data":1}'
INDIR=/tmp/${TESTFILE}/1-in-dir
OUTDIR=/tmp/${TESTFILE}/1-out-dir
mkdir -p "${INDIR}"
mkdir -p "${OUTDIR}"
cd /tmp/${TESTFILE}
/bin/sh ./generate-envoy-yaml.sh "${INDIR}" "${OUTDIR}"
ec=$?
if [ ${ec} -ne 0 ]; then
  echo "non-zero exit code: ${ec}" >> ${ERROR_FILE}
fi
if [ ! -f "${SUCCESS_FILE1}" -o "ran" != "$( cat ${SUCCESS_FILE1} )" ] ; then
  echo "did not run generate_template_input_data.py" >> ${ERROR_DIR}/${TESTFILE}-1.txt
fi
if [ ! -f "${ARGS_FILE1}" -o ! -z "$( cat ${ARGS_FILE1} )" ] ; then
  echo "incorrect invocation arguments to generate_template_input_data.py" >> ${ERROR_FILE}
  cat ${ARGS_FILE1} >> ${ERROR_FILE}
fi
if [ ! -f ${OUTDIR}/input.json ] ; then
  echo "did not create ${OUTDIR}/input.json" >> ${ERROR_FILE}
elif [ "${MOCK_DATA1}" != "$( cat ${OUTDIR}/input.json )" ] ; then
  echo "incorrect input.json contents:" >> ${ERROR_FILE}
  echo "---------- start [" >> ${ERROR_FILE}
  cat ${OUTDIR}/input.json >> ${ERROR_FILE}
  echo "] end ----------" >> ${ERROR_FILE}
fi


# TEST 2 - invoke the generate script with exit code 0
ERROR_FILE=${ERROR_DIR}/${TESTFILE}-2.txt
echo "Need test" >> ${ERROR_FILE}

# TEST 3 - json output fails
ERROR_FILE=${ERROR_DIR}/${TESTFILE}-3.txt
echo "Need test" >> ${ERROR_FILE}


# TEST 4 - the config generation fails
ERROR_FILE=${ERROR_DIR}/${TESTFILE}-4.txt
echo "Need test" >> ${ERROR_FILE}
