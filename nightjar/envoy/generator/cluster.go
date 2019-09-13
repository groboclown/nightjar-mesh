package generator

import (
	"fmt"
	"time"

	"github.com/gogo/protobuf/types"

	v2 "github.com/envoyproxy/go-control-plane/envoy/api/v2"
	"github.com/envoyproxy/go-control-plane/envoy/api/v2/auth"
	"github.com/envoyproxy/go-control-plane/envoy/api/v2/core"
	"github.com/envoyproxy/go-control-plane/envoy/api/v2/endpoint"
	"github.com/envoyproxy/go-control-plane/envoy/api/v2/listener"
	"github.com/envoyproxy/go-control-plane/envoy/api/v2/route"
	als "github.com/envoyproxy/go-control-plane/envoy/config/accesslog/v2"
	alf "github.com/envoyproxy/go-control-plane/envoy/config/filter/accesslog/v2"
	hcm "github.com/envoyproxy/go-control-plane/envoy/config/filter/network/http_connection_manager/v2"
	tcp "github.com/envoyproxy/go-control-plane/envoy/config/filter/network/tcp_proxy/v2"
	"github.com/envoyproxy/go-control-plane/pkg/cache"
	"github.com/envoyproxy/go-control-plane/pkg/util"

	"github.com/groboclown/nightjar-mesh/nightjar/envoy"
)


// Create the endpoint described by the arguments
func MakeEndpoint(hostIP string, port uint32) *v2.ClusterLoadAssignment {
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


func MakeLoadAssignment(cluster *envoy.ServceCluster) *v2.ClusterLoadAssignment {
	endpoints := make([]*endpoint.LbEndpoint)
	for _, service := cluster.Endpoints {
		endpoints = endpoints.append(service.HostIP, service.HostPort)
	}

	return &v2.ClusterLoadAssignment{
		ClusterName: clusterName,
		Endpoints: []*endpoint.LocalityLbEndpoints{{
			LbEndpoints: endpoints
		}},
	}
}



// MakeCluster creates a cluster using either ADS or EDS.
func MakeCluster(cluster *envoy.ServiceCluster) *v2.Cluster {
	connectTimeout := 5 * time.Second
	http1 := &core.Http1ProtocolOptions{}
	var http2 *core.Http2ProtocolOptions := nil
	if ! cluster.Http1Only {
		http2 = &core.Http2ProtocolOptions{}
	}
	
	return &v2.Cluster{
		Name:                 cluster.ServiceName,
		ConnectTimeout:       &connectTimeout,
		ClusterDiscoveryType: &v2.Cluster_Type{Type: v2.Cluster_STATIC}, // uses IP only
		ProtocolSelection:    Cluster_USE_CONFIGURED_PROTOCOL,
		LoadAssignment:       MakeLoadAssignment(cluster),
		HttpProtocolOptions:  http1,
		Http2ProtocolOptions: http2,

		// TODO add in option for TlsContext
	}
}
