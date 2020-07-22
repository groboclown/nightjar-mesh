
"""
Utility functions to aid with implementing new data stores.

The functions allow for two general techniques of storage

* a "wide" model, where each entity is its own resource, and the path of the
    resource indicates the details.
* a "single" model, where each version is a single data blob.
"""

from . import wide
