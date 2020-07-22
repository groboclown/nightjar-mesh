
"""
Extension point common utilities.
"""

from typing import Sequence, Callable
import os
import shlex
import shutil
import time


def get_env_executable_cmd(env_name: str) -> Sequence[str]:
    """
    Gets the executable command list from the environment variable with the given name.
    If the environment variable is not set, or the executable (first argument of the string)
    is not found, an Exception is raised.

    @param env_name: environment variable name.
    @return:
    """
    exec_env_value = os.environ.get(env_name)
    if not exec_env_value:
        raise Exception('No environment variable `{0}`'.format(env_name))
    cmd = shlex.split(exec_env_value)
    executable = shutil.which(cmd[0])
    if executable is None:
        raise Exception('No such executable: {0} (from environment variable {1})'.format(
            cmd[0], env_name,
        ))
    return (executable, *cmd[1:],)


def run_with_backoff(
        runner_callback: Callable[[], int],
        requires_retry_callback: Callable[[int], bool],
        maximum_retries: int,
        maximum_wait: float,
        sleep_func: Callable[[float], None] = time.sleep,
) -> int:
    """
    Runs the command, and if it requires a retry, then it retries with a wait.  However,
    the exponential wait is in seconds.

    The logic is taken from:
    https://docs.aws.amazon.com/general/latest/gr/api-retries.html

    @param sleep_func:
    @param maximum_wait:
    @param runner_callback:
    @param requires_retry_callback:
    @param maximum_retries:
    @return:
    """
    retry_count = 0
    keep_running = True
    result = -1
    while keep_running and retry_count < maximum_retries:
        retry_count += 1
        result = runner_callback()
        if requires_retry_callback(result) and retry_count < maximum_retries:
            sleep_time = min((2 ** retry_count), maximum_wait)
            sleep_func(sleep_time)
        else:
            keep_running = False
    return result
