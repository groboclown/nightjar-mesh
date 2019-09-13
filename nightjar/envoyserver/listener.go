package envoyserver

// Mostly taken from the envoy go-control-plane code,
// envoy/pkg/test/resource/resource.go
// and
// envoy/pkg/test/resource/secret.go

// Both of those are under this license:

// Copyright 2018 Envoyproxy Authors
//
//   Licensed under the Apache License, Version 2.0 (the "License");
//   you may not use this file except in compliance with the License.
//   You may obtain a copy of the License at
//
//       http://www.apache.org/licenses/LICENSE-2.0
//
//   Unless required by applicable law or agreed to in writing, software
//   distributed under the License is distributed on an "AS IS" BASIS,
//   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//   See the License for the specific language governing permissions and
//   limitations under the License.

// Package resource creates test xDS resources

import (
	"fmt"

	"github.com/gogo/protobuf/types"

	v2 "github.com/envoyproxy/go-control-plane/envoy/api/v2"
	"github.com/envoyproxy/go-control-plane/envoy/api/v2/core"
	"github.com/envoyproxy/go-control-plane/envoy/api/v2/listener"
	"github.com/envoyproxy/go-control-plane/envoy/api/v2/route"
	// alf "github.com/envoyproxy/go-control-plane/envoy/config/filter/accesslog/v2"
	hcm "github.com/envoyproxy/go-control-plane/envoy/config/filter/network/http_connection_manager/v2"
	"github.com/envoyproxy/go-control-plane/pkg/util"
)

const (
	allNetworks = "0.0.0.0"
)


// MakeRouteConfig creates an HTTP route that routes to a given cluster.
func MakeRouteConfig(routeName string, clusters []*ServiceCluster) *v2.RouteConfiguration {
	routes := make([]*route.Route, 0)
	for _, cluster := range clusters {
		for _, path := range cluster.Paths {
			routes = append(routes, &route.Route{
				Match: &route.RouteMatch{
					PathSpecifier: &route.RouteMatch_Prefix{
						Prefix: path,
					},
				},
				Action: &route.Route_Route{
					Route: &route.RouteAction{
						ClusterSpecifier: &route.RouteAction_Cluster{
							Cluster: cluster.ServiceName,
						},
					},
				},
			})
		}
	}

	return &v2.RouteConfiguration{
		Name: routeName,
		ValidateClusters: &types.BoolValue{Value: true},
		VirtualHosts: []*route.VirtualHost{{
			Name:    routeName,
			Domains: []string{"*"},
			Routes: routes,
		}},
	}
}


// MakeHTTPListener creates a listener with the correct port and routes.
// The `index` parameter allows for add-then-remove usage to prevent gaps where
// nothing is served.
func MakeHTTPListener(index int64, port uint32, clusters []*ServiceCluster) *v2.Listener {
	manager := &hcm.HttpConnectionManager{
		CodecType:  hcm.AUTO,
		StatPrefix: "http",
		HttpFilters: []*hcm.HttpFilter{{
			Name: util.Router,
		}},
		// AccessLog: []*alf.AccessLog{{
		//     Name: util.HTTPGRPCAccessLog,
		//     ConfigType: &alf.AccessLog_TypedConfig{
		//         TypedConfig: alsConfigPbst,
		//     },
		// }},
		RouteSpecifier: &hcm.HttpConnectionManager_RouteConfig{
			RouteConfig: MakeRouteConfig(fmt.Sprintf("route-%d-%d", port, index), clusters),
		},
	}
	pbst, err := types.MarshalAny(manager)
	if err != nil {
		panic(err)
	}

	return &v2.Listener{
		Name: fmt.Sprintf("service-http-%d-%d", port, index),
		Address: &core.Address{
			Address: &core.Address_SocketAddress{
				SocketAddress: &core.SocketAddress{
					Protocol: core.TCP,
					Address:  allNetworks,
					PortSpecifier: &core.SocketAddress_PortValue{
						PortValue: port,
					},
				},
			},
		},
		FilterChains: []*listener.FilterChain{{
			Filters: []*listener.Filter{{
				Name: util.HTTPConnectionManager,
				ConfigType: &listener.Filter_TypedConfig{
					TypedConfig: pbst,
				},
			}},
		}},
	}
}
