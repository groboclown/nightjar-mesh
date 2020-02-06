#!/usr/bin/python3

import os
import sys

with open(os.environ['SUCCESS_FILE2'], 'w') as f:
    f.write('ran\n')
with open(os.environ['ARGS_FILE2'], 'w') as f:
    f.write(' '.join(sys.argv[1:]))
print(os.environ['MOCK_DATA2'])
sys.exit(int(os.environ['MOCK_EXIT_CODE2']))
