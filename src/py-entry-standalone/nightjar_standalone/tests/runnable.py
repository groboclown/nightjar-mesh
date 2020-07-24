#!/usr/bin/python3

"""
Simulates an execution end point.
"""

import shutil
import sys

print("Running with " + repr(sys.argv))
exit_code = int(sys.argv[1])
src_file = sys.argv[2]
tgt_file: str = ''
for arg in sys.argv[3:]:
    if arg.startswith('--output-file='):
        tgt_file = arg[14:]
    elif arg.startswith('--action-file='):
        tgt_file = arg[14:]
if src_file and src_file != 'none' and tgt_file:
    print("Copying {0} to {1}".format(src_file, tgt_file))
    shutil.copy(src_file, tgt_file)
sys.exit(exit_code)
