#!/bin/sh

indir="$1"
outdir="$2"

test -d "${outdir}" && rm -r "${outdir}"
mkdir -p "${outdir}"

echo "Generating the template input data."
export PYTHONPATH="python-src:${PYTHONPATH}"
python3 -m nightjar.cloudmap_collector.standalone > "${outdir}/input.json"
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
          echo "Failed to process envoy configuration file '${i}'."
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
