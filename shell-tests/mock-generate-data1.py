#!/usr/bin/python3

import os
import sys

with open(os.environ['SUCCESS_FILE1'], 'a') as f:
    f.write('ran\n')
with open(os.environ['ARGS_FILE1'], 'a') as f:
    f.write(' '.join(sys.argv[1:]) + '\n')
print(os.environ['MOCK_DATA1'])
sys.exit(int(os.environ['MOCK_EXIT_CODE1']))
