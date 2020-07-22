#!/usr/bin/python3

"""
Generates the schema parsing Python code from the source yaml-formatted schema.
"""

import os
import sys
import fastjsonschema
import yaml
import tempfile
import shutil
import json

schema_dir = os.path.abspath(sys.argv[1])
code_output_dir = sys.argv[2]
temp_dir = tempfile.mkdtemp()
init_contents = '''
"""
Auto-generated validation code.
"""

'''

try:
    print("Dumping into " + temp_dir)
    # Translate the file to JSON format to allow for $ref resolving.
    # Note that the source filename isn't changed, which should be fine.
    for filename in os.listdir(schema_dir):
        if not filename.endswith('-schema.yaml'):
            continue
        with open(os.path.join(schema_dir, filename), 'r') as f:
            schema = yaml.safe_load(f)
        # Required for relative URI parsing.
        schema['$id'] = 'file:' + temp_dir + '/' + filename
        with open(os.path.join(temp_dir, filename), 'w') as f:
            json.dump(schema, f)

    for filename in os.listdir(temp_dir):
        # Remember, the filename is still ending -schema.yaml
        code_name = filename[:-12].replace('-', '_')
        print("Processing " + filename)
        with open(os.path.join(temp_dir, filename), 'r') as f:
            schema = json.load(f)
        code = fastjsonschema.compile_to_code(schema)
        to_replace_src_name_1 = ('file:' + temp_dir + '/').replace(':', '_').replace('/', '_')
        to_replace_src_name_2 = ('file://' + temp_dir + '/').replace(':', '_').replace('/', '_')
        code = (
            code.
            replace(to_replace_src_name_1, '').
            replace(to_replace_src_name_2, '').
            replace('from fastjsonschema ', 'from ..fastjsonschema_replacement ').
            replace('(data):', '(data: Dict[str, Any]) -> Dict[str, Any]:')
        )
        with open(os.path.join(code_output_dir, code_name + '.py'), 'w') as f:
            f.write("# DO NOT MODIFY\n# AUTO-GENERATED CODE.\n\n# pylint: ignore\n\nfrom typing import Dict, Any\n\n")
            f.write(code)
        init_contents += 'from .{0} import validate_{0}_schema_yaml as validate_{0}\n'.format(code_name)

    with open(os.path.join(code_output_dir, '__init__.py'), 'w') as f:
        f.write(init_contents)

finally:
    shutil.rmtree(temp_dir)
