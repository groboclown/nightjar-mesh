#!/bin/sh

mkdir /tmp/${TESTFILE}


cp ${SUITE_DIR}/envoy-docker/nightjar-src/generate-envoy-yaml.sh /tmp/${TESTFILE}/.
cp ${TEST_DIR}/mock-generate-data1.py /tmp/${TESTFILE}/generate_template_input_data.py
mkdir -p /tmp/${TESTFILE}/bin
cp ${TEST_DIR}/mock-script2.sh /tmp/${TESTFILE}/bin/pystache
chmod +x /tmp/${TESTFILE}/bin/pystache
export PATH="/tmp/${TESTFILE}/bin:${PATH}"


# TEST 1 - invoke the generate script with exit code 0 and no files to process
ERROR_FILE=${ERROR_DIR}/${TESTFILE}-1.txt

# exec file 1: data generator
export SUCCESS_FILE1=/tmp/${TESTFILE}/1-ran1.txt
export ARGS_FILE1=/tmp/${TESTFILE}/1-args1.txt
test -e "${SUCCESS_FILE1}" && rm -r "${SUCCESS_FILE1}"
test -e "${ARGS_FILE1}" && rm -r "${ARGS_FILE1}"
export MOCK_EXIT_CODE1=0
export MOCK_DATA1='{"the-json-data":1}'

# exec file 2: pystache
# should never be run.
export SUCCESS_FILE2=/tmp/${TESTFILE}/1-ran2.txt
export ARGS_FILE2=/tmp/${TESTFILE}/1-args2.txt
test -e "${SUCCESS_FILE2}" && rm -r "${SUCCESS_FILE2}"
test -e "${ARGS_FILE2}" && rm -r "${ARGS_FILE2}"
export MOCK_EXIT_CODE2=1

INDIR=/tmp/${TESTFILE}/1-in-dir
OUTDIR=/tmp/${TESTFILE}/1-out-dir
test -e ${INDIR} && rm -r ${INDIR}
mkdir -p "${INDIR}"
test -e ${OUTDIR} && rm -r ${OUTDIR}
mkdir -p "${OUTDIR}"
cd /tmp/${TESTFILE}
/bin/sh ./generate-envoy-yaml.sh "${INDIR}" "${OUTDIR}"
ec=$?
if [ ${ec} -ne 0 ]; then
  echo "non-zero exit code: ${ec}" >> ${ERROR_FILE}
fi
if [ ! -f "${SUCCESS_FILE1}" -o "ran" != "$( cat ${SUCCESS_FILE1} )" ] ; then
  echo "did not run generate_template_input_data.py" >> ${ERROR_FILE}
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
if [ -f "${SUCCESS_FILE2}" ] ; then
  echo "incorrectly ran pystache when there were no files to process" >> ${ERROR_FILE}
fi



# TEST 2 - invoke the generate script with exit code 0
ERROR_FILE=${ERROR_DIR}/${TESTFILE}-2.txt

# exec file 1: data generator
export SUCCESS_FILE1=/tmp/${TESTFILE}/2-ran1.txt
export ARGS_FILE1=/tmp/${TESTFILE}/2-args1.txt
test -f "${SUCCESS_FILE1}" && rm "${SUCCESS_FILE1}"
test -f "${ARGS_FILE1}" && rm "${ARGS_FILE1}"
export MOCK_EXIT_CODE1=0
export MOCK_DATA1='{"the-json-data":2}'

# exec file 2: pystache
export SUCCESS_FILE2=/tmp/${TESTFILE}/2-ran2.txt
export ARGS_FILE2=/tmp/${TESTFILE}/2-args2.txt
export PID_FILE2=/tmp/${TESTFILE}/2-pid2.txt
test -e ${SUCCESS_FILE2} && rm -r ${SUCCESS_FILE2}
test -e ${ARGS_FILE2} && rm -r ${ARGS_FILE2}
test -e ${PID_FILE2} && rm -r ${PID_FILE2}
export MOCK_EXIT_CODE2=0
export MOCK_DATA2='the-mustache-output'

INDIR=/tmp/${TESTFILE}/2-in-dir
OUTDIR=/tmp/${TESTFILE}/2-out-dir

test -e ${INDIR} && rm -r ${INDIR}
mkdir -p ${INDIR}
test -e ${OUTDIR} && rm -r ${OUTDIR}
mkdir -p ${OUTDIR}
echo 'a1' > ${INDIR}/a1.txt
echo 'a2' > ${INDIR}/a2.txt.mustache
mkdir -p ${INDIR}/d1
echo 'd1' > ${INDIR}/d1/d1.txt
echo 'd2' > ${INDIR}/d1/d2.txt.mustache
cd /tmp/${TESTFILE}
/bin/sh ./generate-envoy-yaml.sh "${INDIR}" "${OUTDIR}"
ec=$?
if [ ${ec} -ne 0 ]; then
  echo "non-zero exit code: ${ec}" >> ${ERROR_FILE}
fi
if [ ! -f "${SUCCESS_FILE1}" -o "ran" != "$( cat ${SUCCESS_FILE1} )" ] ; then
  echo "did not run generate_template_input_data.py" >> ${ERROR_FILE}
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
if [ ! -f "${SUCCESS_FILE2}" -o "ran" != "$( cat ${SUCCESS_FILE2} )" ] ; then
  echo "did not run pystache 1 time" >> ${ERROR_FILE}
fi
if [ ! -f "${ARGS_FILE2}" -o "${INDIR}/a2.txt.mustache ${OUTDIR}/input.json" != "$( cat ${ARGS_FILE2} )" ] ; then
  echo "incorrect invocation arguments to pystache" >> ${ERROR_FILE}
  cat ${ARGS_FILE2} >> ${ERROR_FILE}
fi
if [ -f ${OUTDIR}/a2.txt.mustache ] ; then
  echo "Incorrectly copied a mustache file into the output directory." >> ${ERROR_FILE}
fi
if [ ! -f ${OUTDIR}/a2.txt -o "${MOCK_DATA2}" != "$( cat ${OUTDIR}/a2.txt )" ] ; then
  echo "Did not copy and populate output mustache file" >> ${ERROR_FILE}
fi
if [ ! -f ${OUTDIR}/a1.txt ] ; then
  echo "Did not copy non-mustache file into the output directory." >> ${ERROR_FILE}
fi
if [ ! -f ${OUTDIR}/d1/d1.txt ] ; then
  echo "Did not copy subdirectory contents into the output directory." >> ${ERROR_FILE}
fi
if [ ! -f ${OUTDIR}/d1/d2.txt.mustache ] ; then
  echo "Did not copy subdirectory contents, including mustache files, into the output directory." >> ${ERROR_FILE}
fi



# TEST 3 - json output fails
ERROR_FILE=${ERROR_DIR}/${TESTFILE}-3.txt

# exec file 1: data generator
export SUCCESS_FILE1=/tmp/${TESTFILE}/3-ran1.txt
export ARGS_FILE1=/tmp/${TESTFILE}/3-args1.txt
test -f "${SUCCESS_FILE1}" && rm "${SUCCESS_FILE1}"
test -f "${ARGS_FILE1}" && rm "${ARGS_FILE1}"
export MOCK_EXIT_CODE1=1
export MOCK_DATA1='{"the-json-data":3}'

# exec file 2: pystache
# Should never be run.
export SUCCESS_FILE2=/tmp/${TESTFILE}/3-ran2.txt
export ARGS_FILE2=/tmp/${TESTFILE}/3-args2.txt
export PID_FILE2=/tmp/${TESTFILE}/3-pid2.txt
test -e ${SUCCESS_FILE2} && rm -r ${SUCCESS_FILE2}
test -e ${ARGS_FILE2} && rm -r ${ARGS_FILE2}
test -e ${PID_FILE2} && rm -r ${PID_FILE2}
export MOCK_EXIT_CODE2=2
export MOCK_DATA2='the-mustache-output'

INDIR=/tmp/${TESTFILE}/3-in-dir
OUTDIR=/tmp/${TESTFILE}/3-out-dir

test -e ${INDIR} && rm -r ${INDIR}
mkdir -p ${INDIR}
test -e ${OUTDIR} && rm -r ${OUTDIR}
mkdir -p ${OUTDIR}
cd /tmp/${TESTFILE}
/bin/sh ./generate-envoy-yaml.sh "${INDIR}" "${OUTDIR}"
ec=$?
if [ ${ec} -eq 0 ]; then
  echo "Wrong exit code: ${ec}" >> ${ERROR_FILE}
fi
if [ ! -f "${SUCCESS_FILE1}" -o "ran" != "$( cat ${SUCCESS_FILE1} )" ] ; then
  echo "did not run generate_template_input_data.py" >> ${ERROR_FILE}
fi
if [ ! -f "${ARGS_FILE1}" -o ! -z "$( cat ${ARGS_FILE1} )" ] ; then
  echo "incorrect invocation arguments to generate_template_input_data.py" >> ${ERROR_FILE}
  cat ${ARGS_FILE1} >> ${ERROR_FILE}
fi
if [ -f "${SUCCESS_FILE2}" ] ; then
  echo "incorrectly ran pystache when the data generation failed" >> ${ERROR_FILE}
fi



# TEST 4 - the config generation fails
ERROR_FILE=${ERROR_DIR}/${TESTFILE}-4.txt

# exec file 1: data generator
export SUCCESS_FILE1=/tmp/${TESTFILE}/4-ran1.txt
export ARGS_FILE1=/tmp/${TESTFILE}/4-args1.txt
test -f "${SUCCESS_FILE1}" && rm "${SUCCESS_FILE1}"
test -f "${ARGS_FILE1}" && rm "${ARGS_FILE1}"
export MOCK_EXIT_CODE1=0
export MOCK_DATA1='{"the-json-data":4}'

# exec file 2: pystache
export SUCCESS_FILE2=/tmp/${TESTFILE}/4-ran2.txt
export ARGS_FILE2=/tmp/${TESTFILE}/4-args2.txt
export PID_FILE2=/tmp/${TESTFILE}/4-pid2.txt
test -e ${SUCCESS_FILE2} && rm -r ${SUCCESS_FILE2}
test -e ${ARGS_FILE2} && rm -r ${ARGS_FILE2}
test -e ${PID_FILE2} && rm -r ${PID_FILE2}
export MOCK_EXIT_CODE2=1
export MOCK_DATA2='the-mustache-output'

INDIR=/tmp/${TESTFILE}/4-in-dir
OUTDIR=/tmp/${TESTFILE}/4-out-dir

test -e ${INDIR} && rm -r ${INDIR}
mkdir -p ${INDIR}
test -e ${OUTDIR} && rm -r ${OUTDIR}
mkdir -p ${OUTDIR}
echo 'a2' > ${INDIR}/a2.txt.mustache
cd /tmp/${TESTFILE}
/bin/sh ./generate-envoy-yaml.sh "${INDIR}" "${OUTDIR}"
ec=$?
if [ ${ec} -eq 0 ]; then
  echo "Wrong exit code: ${ec}" >> ${ERROR_FILE}
fi
if [ ! -f "${SUCCESS_FILE1}" -o "ran" != "$( cat ${SUCCESS_FILE1} )" ] ; then
  echo "did not run generate_template_input_data.py" >> ${ERROR_FILE}
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
if [ ! -f "${SUCCESS_FILE2}" -o "ran" != "$( cat ${SUCCESS_FILE2} )" ] ; then
  echo "did not run pystache 1 time" >> ${ERROR_FILE}
fi
if [ ! -f "${ARGS_FILE2}" -o "${INDIR}/a2.txt.mustache ${OUTDIR}/input.json" != "$( cat ${ARGS_FILE2} )" ] ; then
  echo "incorrect invocation arguments to pystache" >> ${ERROR_FILE}
  cat ${ARGS_FILE2} >> ${ERROR_FILE}
fi
