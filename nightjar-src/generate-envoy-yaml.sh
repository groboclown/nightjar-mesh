#!/bin/sh

outfile="$1"

test -f "$outfile" && rm "$outfile"

echo "Generating the template input data."
python3 ./generate_template_input_data.py > /tmp/input.json
if [ $? -ne 0 ] ; then
  echo "Failed to generate the template input data."
  exit 1
fi

echo "Generating the envoy configuration file."
python3 ./generate_envoy_configuration.py /tmp/input.json "$ENVOY_CONFIGURATION_TEMPLATE" > "$outfile"
if [ $? -ne 0 ] ; then
  echo "Failed to generate envoy configuration file."
  exit 1
fi
exit 0
