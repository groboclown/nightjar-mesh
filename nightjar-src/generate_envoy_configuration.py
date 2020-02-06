#!/usr/bin/python3

import json
import sys
from typing import Sequence
import pystache


# ---------------------------------------------------------------------------
def main(args: Sequence[str]) -> int:
    json_data_filename, template_filename = args

    with open(template_filename, 'r') as f:
        template = f.read()

    with open(json_data_filename, 'r') as f:
        context = json.load(f)

    pystache.defaults.TAG_ESCAPE = lambda u: u.replace('"', '\\"')
    print(pystache.render(template, context))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
