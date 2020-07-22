
"""
Data Store for simple, flat files, stored locally.

This stores one copy of the templates and configurations.  These are
just JSON formatted files.

The template storage file is located in the environment variable `DM_LOCAL__TEMPLATE_FILE`,
and if that is not given, then the default `/etc/data-store/templates.json` is used.

The configuration storage file is located in the environment variable
`DM_LOCAL__CONFIGURATION_FILE`, and if that is not given, then the default
`/etc/data-store/configurations.json` is used.

"""
