
"""
Memory usage functions.
"""

import sys


def get_current_memory_usage() -> int:
    """ Memory usage in kB """
    try:
        with open('/proc/self/status') as f:
            memusage = f.read().split('VmRSS:')[1].split('\n')[0][:-3]

        return int(memusage.strip())
    except IOError:
        return -1


def report_current_memory_usage() -> None:
    """Report to stderr the current memory usage."""
    mem_usage = get_current_memory_usage()
    if mem_usage >= 0:
        sys.stderr.write('-- Current memory usage: {0} kB\n'.format(mem_usage))
