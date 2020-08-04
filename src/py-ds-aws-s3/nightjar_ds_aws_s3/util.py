
"""Constant values"""

DATA_FILE_EXTENSION = '.data'
META_FILE_EXTENSION = '.meta'
FILE_EXTENSION_LENGTH = 5


def get_version_from_data_key_name(key: str) -> str:
    """Extract the version from the key name for the given data or meta."""
    assert key.endswith(DATA_FILE_EXTENSION) or key.endswith(META_FILE_EXTENSION)
    if '/' in key:
        key = key[key.rindex('/') + 1:]
    return key[:-FILE_EXTENSION_LENGTH]


def is_data_file(key: str) -> bool:
    """Is the key a data file?"""
    return key.endswith(DATA_FILE_EXTENSION)


def is_meta_file(key: str) -> bool:
    """Is the key a data file?"""
    return key.endswith(META_FILE_EXTENSION)
