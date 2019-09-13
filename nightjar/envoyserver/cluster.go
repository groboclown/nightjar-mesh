package envoyserver

import (
	"time"

	v2 "github.com/envoyproxy/go-control-plane/envoy/api/v2"
	"github.com/envoyproxy/go-control-plane/envoy/api/v2/core"
	"github.com/envoyproxy/go-control-plane/envoy/api/v2/endpoint"
)


// Create the endpoint described by the arguments
func MakeEndpoint(hostIP string, port uint32) *endpoint.LbEndpoint {
	return &endpoint.LbEndpoint{
		HostIdentifier: &endpoint.LbEndpoint_Endpoint{
			Endpoint: &endpoint.Endpoint{
				Address: &core.Address{
					Address: &core.Address_SocketAddress{
						SocketAddress: &core.SocketAddress{
							Protocol: core.TCP,
							Address:  hostIP,
							PortSpecifier: &core.SocketAddress_PortValue{
								PortValue: port,
							},
						},
					},
				},
			},
		},
	}
}


func MakeLoadAssignment(cluster *ServiceCluster) *v2.ClusterLoadAssignment {
	endpoints := make([]*endpoint.LbEndpoint, 0)
	for _, service := range cluster.Endpoints {
		endpoints = append(endpoints, MakeEndpoint(service.HostIP, service.HostPort))
	}

	return &v2.ClusterLoadAssignment{
		ClusterName: cluster.ServiceName,
		Endpoints: []*endpoint.LocalityLbEndpoints{{
			LbEndpoints: endpoints,
		}},
	}
}



// MakeCluster creates a cluster using either ADS or EDS.
func MakeCluster(cluster *ServiceCluster) *v2.Cluster {
	connectTimeout := 5 * time.Second
	http1 := &core.Http1ProtocolOptions{}
	var http2 *core.Http2ProtocolOptions = nil
	if ! cluster.Http1Only {
		http2 = &core.Http2ProtocolOptions{}
	}
	
	return &v2.Cluster{
		Name:                 cluster.ServiceName,
		ConnectTimeout:       &connectTimeout,
		ClusterDiscoveryType: &v2.Cluster_Type{Type: v2.Cluster_STATIC}, // uses IP only
		ProtocolSelection:    v2.Cluster_USE_CONFIGURED_PROTOCOL,
		LoadAssignment:       MakeLoadAssignment(cluster),
		HttpProtocolOptions:  http1,
		Http2ProtocolOptions: http2,

		// TODO add in option for TlsContext
	}
}
