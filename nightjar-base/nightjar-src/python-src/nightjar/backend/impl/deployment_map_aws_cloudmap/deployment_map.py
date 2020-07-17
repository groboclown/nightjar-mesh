
"""
The deployment map implementation for AWS cloudmap service discovery
"""

from typing import List, Iterable, Dict, Optional, Tuple
from .config import AwsCloudmapConfig
from .service_discovery import (
    DiscoveryServiceNamespace,
    DiscoveryServiceColor,
    load_namespaces,
    set_aws_config,
)
from ...api.deployment_map.service_data import (
    EnvoyConfig,
    EnvoyCluster,
    EnvoyClusterEndpoint,
    EnvoyListener,
    EnvoyRoute,
)
from ...api.deployment_map.abc_depoyment_map import (
    AbcDeploymentMap, NamedProtectionPort, ServiceDef,
)
from ....msg import warn


class ServiceDiscoveryDeploymentMap(AbcDeploymentMap):
    """
    Maps between the AWS Cloud Map Service Discovery, with custom extensions used by
    nightjar, to the Envoy configuration input data schema.
    """

    def __init__(
            self,
            config: AwsCloudmapConfig,
            namespaces: Iterable[str],
    ) -> None:
        """
        The list of namespaces to search.  By pre-loading this list, it makes the total
        lookup use fewer requests.

        The namespace allows for either an arn (prefix in the string is 'arn:'), a namespace id
        (prefix in the string of 'id:'), or a namespace "name".  The name will require an
        additional lookup to get the ID, so it's preferable to give an arn or id.

        """
        set_aws_config(config)
        self.namespace_cache = load_namespaces(namespaces, [])[1]

    def load_services_in_namespaces(
            self, namespaces: Iterable[str],
    ) -> Dict[str, Iterable[ServiceDef]]:
        loaded_namespaces, new_cache = load_namespaces(namespaces, self.namespace_cache)
        self.namespace_cache = new_cache
        ret: Dict[str, Iterable[ServiceDef]] = {}
        for key, n_s in loaded_namespaces.items():
            n_s.load_services(False)
            ret[key] = [
                ServiceDef(
                    svc.namespace_id, svc.service_id,
                    svc.group_service_name or 'default',
                    svc.group_color_name or 'default',
                )
                for svc in n_s.services
            ]
        return ret

    def load_service_config(
            self, local_namespace: str, service_id_port: NamedProtectionPort,
            external_namespace_ports: Iterable[NamedProtectionPort],
            force_cache_refresh: bool = False,
    ) -> EnvoyConfig:
        """
        Construct the listener groups, which are per namespace, and the clusters
        referenced by the listeners.

        In order to support better envoy cluster traffic management, each
        service/color is its own cluster.
        """
        output_listeners: List[EnvoyListener] = []
        output_clusters: List[EnvoyCluster] = []

        # -------------------------------------------------------------------
        loaded_service, loaded_namespace, external_namespaces = self.load_services(
            service_id_port, external_namespace_ports, force_cache_refresh,
        )
        if not loaded_service:
            # TODO better exception?
            raise ValueError(
                (
                    'Could not find service {0}?  Could be a changed configuration after request.'
                ).format(service_id_port[0]),
            )
        if not loaded_namespace:
            # TODO better exception?
            raise ValueError(
                (
                    'Could not find service namespace {0}?  Could be a changed '
                    'configuration after request.'
                ).format(loaded_service.namespace_id),
            )

        # -------------------------------------------------------------------
        # Collate the requested services into an envoy configuration.

        local_routes: Dict[str, Dict[str, int]] = {}
        loaded_namespace.load_services(force_cache_refresh)
        for service_color in loaded_namespace.services:
            if (
                    service_color.group_service_name == loaded_service.group_service_name
            ):
                # The local service should never be directed outbound.
                continue
            service_color.load_instances(force_cache_refresh)
            if not service_color.instances:
                warn(
                    "Cluster {s}-{c} has no discovered instances",
                    s=service_color.group_service_name,
                    c=service_color.group_color_name,
                )
            endpoints = []
            for sci in service_color.instances:
                if sci.ipv4:
                    endpoints.append(EnvoyClusterEndpoint(sci.ipv4, sci.port_str))
            cluster = EnvoyCluster(
                '{0}-{1}'.format(service_color.group_service_name, service_color.group_color_name),
                service_color.uses_http2, endpoints,
            )
            if service_color.path_protect_weights:
                output_clusters.append(cluster)
                for path, protect, weight in service_color.path_protect_weights:
                    if protect == service_id_port[1]:
                        if path not in local_routes:
                            local_routes[path] = {}
                        local_routes[path][cluster.cluster_name] = weight
            envoy_routes = [
                EnvoyRoute(path, cluster_weights)
                for path, cluster_weights in local_routes.items()
            ]
            listener = EnvoyListener(service_id_port[2], envoy_routes)
            output_listeners.append(listener)

        for namespace, npp in external_namespaces:
            routes: Dict[str, Dict[str, int]] = {}
            namespace.load_services(force_cache_refresh)
            for service_color in namespace.services:
                service_color.load_instances(force_cache_refresh)
                if not service_color.instances:
                    warn(
                        "Cluster {s}-{c} has no discovered instances",
                        s=service_color.group_service_name,
                        c=service_color.group_color_name,
                    )
                endpoints = []
                for sci in service_color.instances:
                    if sci.ipv4:
                        endpoints.append(EnvoyClusterEndpoint(sci.ipv4, sci.port_str))
                cluster = EnvoyCluster(
                    '{0}-{1}'.format(
                        service_color.group_service_name, service_color.group_color_name,
                    ),
                    service_color.uses_http2, endpoints,
                )
                if service_color.path_protect_weights:
                    output_clusters.append(cluster)
                    for path, protect, weight in service_color.path_protect_weights:
                        if protect == npp[1]:
                            if path not in routes:
                                routes[path] = {}
                            routes[path][cluster.cluster_name] = weight
            envoy_routes = [
                EnvoyRoute(path, cluster_weights)
                for path, cluster_weights in routes.items()
            ]
            listener = EnvoyListener(service_id_port[2], envoy_routes)
            output_listeners.append(listener)
            # Even if there are no routes, still add the listener.
            # During initialization, the dependent containers haven't started yet and may
            # require this proxy to be running before they start.
            listener = EnvoyListener(npp[2], envoy_routes)
            output_listeners.append(listener)

        return EnvoyConfig(output_listeners, output_clusters)

    def load_gateway_envoy_configs(
            self,
            namespaces: Iterable[NamedProtectionPort],
            force_cache_refresh: bool = False,
    ) -> Dict[str, EnvoyConfig]:
        _, _, namespace_npp = self.load_services(None, namespaces, force_cache_refresh)

        ret: Dict[str, EnvoyConfig] = {}
        for namespace, npp in namespace_npp:
            clusters: List[EnvoyCluster] = []
            routes: Dict[str, Dict[str, int]] = {}

            namespace.load_services(False)
            for service_color in namespace.services:
                service_color.load_instances(False)
                if not service_color.instances:
                    warn(
                        "Cluster {s}-{c} has no discovered instances",
                        s=service_color.group_service_name,
                        c=service_color.group_color_name,
                    )
                endpoints: List[EnvoyClusterEndpoint] = []
                for sci in service_color.instances:
                    if sci.ipv4:
                        endpoints.append(EnvoyClusterEndpoint(sci.ipv4, sci.port_str))
                cluster = EnvoyCluster(
                    '{0}-{1}'.format(
                        service_color.group_service_name,
                        service_color.group_color_name,
                    ),
                    service_color.uses_http2, endpoints,
                )
                if service_color.path_protect_weights:
                    clusters.append(cluster)
                    for path, protect, weight in service_color.path_protect_weights:
                        if protect == npp[1]:
                            if path not in routes:
                                routes[path] = {}
                            routes[path][cluster.cluster_name] = weight
            envoy_routes: List[EnvoyRoute] = [
                EnvoyRoute(path, cluster_weights)
                for path, cluster_weights in routes.items()
            ]
            # Even if there are no routes, still add the listener.
            # During initialization, the dependent containers haven't started yet and may
            # require this proxy to be running before they start.
            listener = EnvoyListener(npp[2], envoy_routes)
            ret[npp[0]] = EnvoyConfig([listener], clusters)

        return ret

    def load_services(
            self,
            service_id_port: Optional[NamedProtectionPort],
            external_namespace_ports: Iterable[NamedProtectionPort],
            force_cache_refresh: bool,
    ) -> Tuple[
        Optional[DiscoveryServiceColor],
        Optional[DiscoveryServiceNamespace],
        List[Tuple[DiscoveryServiceNamespace, NamedProtectionPort]],
    ]:  # pylint: disable=R0912, R0915
        """Gets all the services in all the namespaces as possible."""
        # TODO simplify this code, or break it into smaller, more easily tested, chunks.

        # Initial discovery work, to match the requested data with the
        # Service Discovery data.

        remaining_external: Dict[str, NamedProtectionPort] = {
            npp[0]: npp for npp in external_namespace_ports
        }
        external_namespaces: List[Tuple[DiscoveryServiceNamespace, NamedProtectionPort]] = []

        #   First phase:
        #         For each requested namespace, figure out if it's in the list of known
        #         namespaces, if it's an easily figured out namespace-id, or if it's an
        #         unknown namespace name.  Everything that's in the unknown namespace
        #         names, load those namespaces.  This could be joined into the existing
        #         DiscoveryServiceNamespace code.

        requested_ns, all_known_ns = load_namespaces(
            remaining_external.keys(), self.namespace_cache,
        )
        self.namespace_cache = all_known_ns

        #   Second phase:
        #         Load all the services for all the namespaces requested.
        #         If the local service is given and it's not in the loaded services,
        #         then explicitly load that one and its namespace's service.

        local_namespace: Optional[DiscoveryServiceNamespace] = None
        local_service: Optional[DiscoveryServiceColor] = None

        # Note: looking only at the requested namespace values, not all of them,
        # to reduce the number of load_service calls.
        # This may result in an extra loading of the local service when the
        # cache means it isn't necessary.
        # TODO look at a way to optimize this.  It may mean caching the
        #   service_id-to-namespace_id in this class as well.
        for disco_namespace in requested_ns.values():
            disco_namespace.load_services(force_cache_refresh)
            is_local_service = False
            if service_id_port and not local_service:
                local_service = disco_namespace.find_cached_service_with_id(service_id_port[0])
                if local_service:
                    # Found the local service mesh
                    local_namespace = disco_namespace
                    is_local_service = True
            if not is_local_service:
                # an external namespace.
                ns_name: Optional[str] = None
                if disco_namespace.namespace_id in remaining_external:
                    ns_name = disco_namespace.namespace_id
                elif disco_namespace.namespace_arn in remaining_external:
                    ns_name = disco_namespace.namespace_arn
                elif 'id:' + disco_namespace.namespace_id in remaining_external:
                    ns_name = 'id:' + disco_namespace.namespace_id
                elif disco_namespace.namespace_name in remaining_external:
                    ns_name = disco_namespace.namespace_name
                if ns_name:
                    npp = remaining_external[ns_name]
                    del remaining_external[ns_name]
                    external_namespaces.append((disco_namespace, npp,))

        if service_id_port and not local_service:
            local_service = DiscoveryServiceColor.from_single_id(service_id_port[0])
        else:
            local_service = None

        if service_id_port and local_service and not local_namespace:
            remaining_external['id:' + local_service.namespace_id] = (
                'id:' + local_service.namespace_id, service_id_port[1], service_id_port[2],
            )

        if remaining_external:
            # Search again; these were extra namespaces not originally given to us.
            other_services, all_known_ns = load_namespaces(
                remaining_external.keys(), self.namespace_cache,
            )
            self.namespace_cache = all_known_ns

            for disco_namespace in other_services.values():
                disco_namespace.load_services(force_cache_refresh)
                if service_id_port and not local_service:
                    local_service = disco_namespace.find_cached_service_with_id(service_id_port[0])
                if local_service and disco_namespace.namespace_id == local_service.namespace_id:
                    # The local service mesh
                    local_namespace = disco_namespace
                else:
                    # an external namespace.
                    ns_name = None
                    if disco_namespace.namespace_id in remaining_external:
                        ns_name = disco_namespace.namespace_id
                    elif disco_namespace.namespace_arn in remaining_external:
                        ns_name = disco_namespace.namespace_arn
                    elif 'id:' + disco_namespace.namespace_id in remaining_external:
                        ns_name = 'id:' + disco_namespace.namespace_id
                    elif disco_namespace.namespace_name in remaining_external:
                        ns_name = disco_namespace.namespace_name
                    if ns_name:
                        npp = remaining_external[ns_name]
                        del remaining_external[ns_name]
                        external_namespaces.append((disco_namespace, npp,))

            if remaining_external:
                raise ValueError(
                    (
                        'Could not find requested external namespaces {0}.  '
                        'Could be a changed configuration after request.'
                    ).format(remaining_external.keys())
                )
        return local_service, local_namespace, external_namespaces
