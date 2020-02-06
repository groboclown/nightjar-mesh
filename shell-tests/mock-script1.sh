#!/bin/sh

echo "ran" > ${SUCCESS_FILE1}
echo "$*" > ${ARGS_FILE1}
echo "$$" > ${PID_FILE1}
exit ${MOCK_EXIT_CODE1:=0}
