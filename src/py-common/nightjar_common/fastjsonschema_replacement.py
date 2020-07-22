
"""
Replaces the exception in fastjsonschema, so that it doesn't need to be required.
"""

from typing import Dict, Optional, Any


class JsonSchemaException(ValueError):
    """Just-Enough replacement exception"""
    def __init__(
            self, message: str,
            value: Optional[Any] = None,
            name: Optional[str] = None,
            definition: Optional[Dict[str, Any]] = None,
            rule: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.value = value
        self.name = name
        self.definition = definition
        self.rule = rule
