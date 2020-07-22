
"""
Data Store API.

Supported data stores for templates and input data.

The data store contains two kinds of files - templates and contents.  The contents are the
extracted version of the template files.  Each service/color has its own set of files, and each
namespace has its own set of files.  There are also "default" versions of the template files.

Because there are multiple files per active configuration, these must be written and accessed in
an atomic manner.  An envoy proxy configuration must not have some files from one configuration
and some from another.  In practice, there isn't a guaranteed way to extract all the necessary
data from AWS in an atomic way, but the files themselves have an interconnection that must
be respected.

The general flow of the configuration works like this:

* A manager uses [manager.py]() to configure the template files in the data store.
    1. uploads the new configuration of template files.
    2. runs "commit" to make the stored template files active (atomic operation).
* A configurator:
    1. reads data from AWS and creates the template input data.
    2. extracts the template files from the data store.
    3. transforms the template files into content files.
    4. stores the content files in the data store.
    5. runs "commit" to make the stored data active (atomic operation).
* A nightjar-enabled envoy proxy container:
    1. extracts the content files for this specific container.
    2. "mv" the files to the final location, as envoy bootstrap describes.  The "mv" command
        is required, because that's the only operation that envoy listens on to see if a
        configuration should be reloaded.

The files are split by purpose.  The required purpose is `envoy-bootstrap-template`, which is the
envoy bootstrap configuration.  The other purposes are the different files that the bootstrap
configuration references.

The base purpose is `envoy-bootstrap-template`.  This purpose has both a template and a content.
The template is used to create the content, and the content is later transformed by the
nightjar-enabled envoy proxy for it specific deployment, but the data keys there are very limited:

* `admin_port` - the administration port, which can be set per container.
* `listener_port` - the port on which the envoy proxy listens for incoming connections to route
    to outbound services.
* The other configuration file purposes.  Each purpose in the bootstrap file is replaced by the
    file path to that content file.  (Maybe?  Still needs to be figured out.)

These replacements are well defined enough to allow for a simple find/replace mechanism.

"""

from .abc_backend import (
    AbcDataStoreBackend,
    Entity,
    ConfigEntity,
    TemplateEntity,
    NamespaceTemplateEntity,
    ServiceColorTemplateEntity,
    GatewayConfigEntity,
    ServiceIdConfigEntity,
    ACTIVITY_TEMPLATE_DEFINITION,
    ACTIVITY_PROXY_CONFIGURATION,
    SUPPORTED_ACTIVITIES,
    as_gateway_config_entity,
    as_service_id_config_entity,
    as_namespace_template_entity,
    as_service_color_template_entity,
    as_config_entity,
    as_template_entity,
)

from .collector import CollectorDataStore, MatchedServiceColorTemplate, MatchedNamespaceTemplate
from .configuration import ConfigurationReaderDataStore, ConfigurationWriterDataStore
from .envoy_proxy import EnvoyProxyDataStore
from .manager import ManagerReadDataStore, ManagerWriteDataStore
