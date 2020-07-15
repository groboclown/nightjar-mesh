#!/bin/bash

set -e

if [ "$1" -ne "docker-based-test" ] ; then
  echo "This script should ONLY be run from within Docker."
  exit 1
fi

cd $( dirname "$0" )/nightjar-central/shell-tests
echo "------------------------------------------------"
echo "Shell Tests: nightjar-central"
bash ./run-tests.sh
cd $( dirname "$0" )/nightjar-standalone/shell-tests
echo "------------------------------------------------"
echo "Shell Tests: nightjar-standalone"
bash ./run-tests.sh
