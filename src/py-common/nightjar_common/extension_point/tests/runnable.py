
"""A runnable python file.
Used for testing the extension point interfaces.

It takes arguments (exit code file, invocation argument file, *).

"""

import sys
import json

if __name__ == '__main__':
    with open(sys.argv[1], 'r') as f:
        exits = json.load(f)
    exit_code = exits.pop(0)
    with open(sys.argv[1], 'w') as f:
        json.dump(exits, f)
    with open(sys.argv[2], 'r') as f:
        calls = json.load(f)
    calls.append(sys.argv[3:])
    with open(sys.argv[2], 'w') as f:
        json.dump(calls, f)
    # print("Exiting with {0}".format(exit_code))
    sys.exit(exit_code)
