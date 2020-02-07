#!/bin/sh

# Run the envoy validation script on the defualt template generation.

# TEST 0 - is envoy even installed?
ERROR_FILE=${ERROR_DIR}/${TESTFILE}-0.txt
which enovy > /dev/null 2>&1
if [ $? -ne 0 ] ; then
  # Envoy is not installed.
  echo "Could not find envoy executable.  Aborting tests" >> ${ERROR_FILE}
  exit 1
fi


# TEST 1 - ensure the test approach is correct.
# Pipe a wrong config file into envoy and ensure the exit code is non-zero.
ERROR_FILE=${ERROR_DIR}/${TESTFILE}-1.txt
envoy --mode validate --config-yaml 'static_resources: { blah: 1 }' >/dev/null 2>&1
ec=$?
if [ ${ec} -eq 0 ] ; then
  echo "Validation did not have bad error code." >> ${ERROR_FILE}
  # Tests can't continue, because their basic assumption about this enovy is wrong.
  exit 1
fi
# Pipe a valid config file into envoy and ensure the exit code is zero.
envoy --mode validate --config-yaml 'static_resources:' >/dev/null 2>&1
ec=$?
if [ ${ec} -ne 0 ] ; then
  echo "Validation did not have good error code (${ec})." >> ${ERROR_FILE}
  # Tests can't continue, because their basic assumption about this enovy is wrong.
  exit 1
fi


# The tests will use sample input json data, piped through mustache,
# envoy --mode validate -c (generated script)
