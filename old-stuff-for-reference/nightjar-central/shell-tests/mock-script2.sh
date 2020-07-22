#!/bin/sh

echo "ran" >> ${SUCCESS_FILE2}
echo "$*" >> ${ARGS_FILE2}
echo "$$" >> ${PID_FILE2}
echo "${MOCK_DATA2}"
exit ${MOCK_EXIT_CODE2:=0}
