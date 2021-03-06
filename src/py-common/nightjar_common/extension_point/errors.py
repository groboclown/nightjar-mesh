
"""Common extension point exceptions"""


class ConfigurationError(Exception):
    """There was a problem with the configuration."""
    def __init__(self, source: str, problem: str) -> None:
        Exception.__init__(
            self,
            '{0}: Incorrect configuration: {1}'.format(source, problem),
        )
        self.source = source
        self.problem = problem


class ExtensionPointRuntimeError(Exception):
    """Running the extension point generated an error."""
    def __init__(self, source: str, action: str, exit_code: int) -> None:
        Exception.__init__(
            self,
            '{0}: Failed running {1} - exited with {2}'.format(source, action, exit_code),
        )
        self.source = source
        self.action = action
        self.exit_code = exit_code


class ExtensionPointTooManyRetries(Exception):
    """Tried too many retries running the extension point."""
    def __init__(self, source: str, action: str) -> None:
        Exception.__init__(self, '{0}: Retried {1} too many times'.format(source, action))
        self.source = source
        self.action = action
