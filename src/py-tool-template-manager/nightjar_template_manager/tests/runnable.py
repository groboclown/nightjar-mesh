#!/usr/bin/python3

"""
Simulates an execution end point.
"""

import os
import shutil
import sys

print("Running with " + repr(sys.argv))
exit_code = int(sys.argv[1])
received_file = sys.argv[2]
generating_file = sys.argv[3]
tgt_file: str = ''
for arg in sys.argv[4:]:
    if arg.startswith('--action-file='):
        tgt_file = arg[14:]

if received_file and tgt_file and os.path.isfile(tgt_file):
    print("Copying {0} to {1}".format(tgt_file, received_file))
    shutil.copy(tgt_file, received_file)

if generating_file and generating_file != 'none' and tgt_file:
    print("Copying {0} to {1}".format(generating_file, tgt_file))
    shutil.copy(generating_file, tgt_file)
sys.exit(exit_code)
