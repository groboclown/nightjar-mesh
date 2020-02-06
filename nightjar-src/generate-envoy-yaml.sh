#!/bin/sh

indir="$1"
outdir="$2"

test -d "${outdir}" && rm -r "${outdir}"
mkdir -p "${outdir}"

echo "Generating the template input data."
python3 ./generate_template_input_data.py > "${outdir}/input.json"
if [ $? -ne 0 ] ; then
  echo "Failed to generate the template input data."
  exit 1
fi

echo "Generating the envoy configuration files."
for i in "${indir}/"* ; do
  if [ -e "$i" ]; then
    case "${i}" in
      *.mustache)
        filename=$( basename "${i}" .mustache )
        pystache "${i}" "${outdir}/input.json" > "${outdir}/${filename}"
        if [ $? -ne 0 ] ; then
          echo "Failed to generate envoy configuration file ${filename}."
          exit 1
        fi
      ;;
      *)
        cp -R "${i}" "${outdir}/." || exit 1
      ;;
    esac
  fi
done
exit 0
