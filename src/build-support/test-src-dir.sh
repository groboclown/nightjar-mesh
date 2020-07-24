#!/bin/bash

cd $( dirname "$0" )
export PYTHONPATH="$(pwd):$(pwd)/../py-common"
if [ ! -d "../$1" ] ; then
  echo "No such package: $1 ($(pwd)/../$1)"
fi
cd "../$1"

mypy_packages=""
lint_packages=""
for path_name in * ; do
  if [ -f "$path_name/__init__.py" ] ; then
    mypy_packages="${mypy_packages} -p $path_name"
    lint_packages="${lint_packages} $path_name"
  fi
done


echo ""
echo ""
echo "============================================================================="
echo "$1"

echo ""
echo "-----------------------------------------------------------------------------"
echo "$1 - MyPy"
python3 -m mypy ${mypy_packages} || exit 1

echo ""
echo "-----------------------------------------------------------------------------"
echo "$1 - Lint"
python3 -m pylint --load-plugins trailing_commas ${lint_packages} || exit 1

echo ""
echo "-----------------------------------------------------------------------------"
echo "$1 - Unit Test"
python3 -m coverage run --source . -m unittest discover -p "*_test.py"
unit_test_res=$?
python3 -m coverage report -m --fail-under 99 || exit 1

exit $unit_test_res
