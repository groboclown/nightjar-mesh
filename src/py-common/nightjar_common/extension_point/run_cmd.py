
"""
Extension point common utilities.
"""

from typing import Dict, Sequence, Callable, Optional
import shlex
import shutil
import time
from .errors import ConfigurationError


def get_env_executable_cmd(
        env: Dict[str, str], env_name: str, default: Optional[str] = None,
) -> Sequence[str]:
    """
    Gets the executable command list from the environment variable with the given name.
    If the environment variable is not set, or the executable (first argument of the string)
    is not found, an Exception is raised.

    @param env: environment
    @param env_name: environment variable name.
    @param default: optional default value.
    @return:
    """
    exec_env_value = env.get(env_name, default)
    if not exec_env_value:
        raise ConfigurationError(env_name, 'environment variable not defined')
    cmd = shlex.split(exec_env_value)
    executable = shutil.which(cmd[0])
    if executable is None:
        raise ConfigurationError(env_name, 'No such executable: `{0}`'.format(cmd[0]))
    return [executable, *cmd[1:]]


def run_with_backoff(
        runner_callback: Callable[[], int],
        maximum_retries: int,
        maximum_wait: float,
        sleep_func: Callable[[float], None] = time.sleep,
) -> int:
    """
    Runs the command, and if it requires a retry, then it retries with a wait.  However,
    the exponential wait is in seconds.

    This is specially designed to work with the extension points, which all have an exit
    code of 31 to indicate a retry is requested.

    The logic is taken from:
    https://docs.aws.amazon.com/general/latest/gr/api-retries.html

    @param sleep_func:
    @param maximum_wait:
    @param runner_callback:
    @param maximum_retries:
    @return:
    """
    retry_count = 0
    keep_running = True
    result = -1
    while keep_running and retry_count < maximum_retries:
        retry_count += 1
        result = runner_callback()
        if result == 31 and retry_count < maximum_retries:
            sleep_time = min((2 ** retry_count), maximum_wait)
            sleep_func(sleep_time)
        else:
            keep_running = False
    return result
