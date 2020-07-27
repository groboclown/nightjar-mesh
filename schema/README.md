# About

Schemas that describe the JSON formatted output from the extension points.  These can also be used as reference for writers of the Envoy configuration template files.

If the schemas are ever changed, this command must be run:

```bash
python3 rebuild-schema-code.py . ../src/py-common/nightjar-common/validation/
```
