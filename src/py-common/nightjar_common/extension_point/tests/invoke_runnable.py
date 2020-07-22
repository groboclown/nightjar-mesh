
"""
Invoke helper for the runnable.py file.
"""


from typing import List, cast
import os
import platform
import json


RUNNABLE_EXECUTABLE: List[str] = [
    'python3',
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'runnable.py'),
]
if platform.system() == 'Windows':  # pragma no cover
    print("Windows runner")
    RUNNABLE_EXECUTABLE[0] = 'python'


class RunnableInvoker:
    """Handles invoking and checking execution of the runnable.py file."""
    def __init__(self, temp_dir: str) -> None:
        self._exit_codes_file = os.path.join(temp_dir, 'exit-codes.json')
        self._argument_file = os.path.join(temp_dir, 'arguments.json')

    def prepare_runnable(
            self,
            exit_codes: List[int],
    ) -> List[str]:
        """Prepares invoking the runnable, with a list of ordered expected exit codes.
        Returns the base execution list."""
        with open(self._exit_codes_file, 'w') as f:
            json.dump(exit_codes, f)
        with open(self._argument_file, 'w') as f:
            json.dump([], f)

        return [
            *RUNNABLE_EXECUTABLE,
            self._exit_codes_file,
            self._argument_file,
        ]

    def get_invoked_arguments(self) -> List[List[str]]:
        """Returns the ordered arguments for each invocation of the runnable."""
        with open(self._argument_file, 'r') as f:
            return cast(List[List[str]], json.load(f))
