package generator

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
)


// MakeRoute creates an HTTP route that routes to a given cluster.
func MakeRoute(routeName, clusterName string, paths []string) *v2.RouteConfiguration {
    
    return &v2.RouteConfiguration{
        Name: routeName,
        VirtualHosts: []*route.VirtualHost{{
            Name:    routeName,
            Domains: []string{"*"},
            Routes: []*route.Route{{
                Match: &route.RouteMatch{
                    PathSpecifier: &route.RouteMatch_Prefix{
                        Prefix: "/",
                    },
                },
                Action: &route.Route_Route{
                    Route: &route.RouteAction{
                        ClusterSpecifier: &route.RouteAction_Cluster{
                            Cluster: clusterName,
                        },
                    },
                },
            }},
        }},
    }
}

// data source configuration
func configSource(mode string) *core.ConfigSource {
    source := &core.ConfigSource{}
    switch mode {
    case Ads:
        source.ConfigSourceSpecifier = &core.ConfigSource_Ads{
            Ads: &core.AggregatedConfigSource{},
        }
    case Xds:
        source.ConfigSourceSpecifier = &core.ConfigSource_ApiConfigSource{
            ApiConfigSource: &core.ApiConfigSource{
                ApiType:                   core.ApiConfigSource_GRPC,
                SetNodeOnFirstMessageOnly: true,
                GrpcServices: []*core.GrpcService{{
                    TargetSpecifier: &core.GrpcService_EnvoyGrpc_{
                        EnvoyGrpc: &core.GrpcService_EnvoyGrpc{ClusterName: XdsCluster},
                    },
                }},
            },
        }
    case Rest:
        source.ConfigSourceSpecifier = &core.ConfigSource_ApiConfigSource{
            ApiConfigSource: &core.ApiConfigSource{
                ApiType:      core.ApiConfigSource_REST,
                ClusterNames: []string{XdsCluster},
                RefreshDelay: &RefreshDelay,
            },
        }
    }
    return source
}

// MakeHTTPListener creates a listener using either ADS or RDS for the route.
func MakeHTTPListener(mode string, listenerName string, port uint32, route string) *v2.Listener {
    rdsSource := configSource(mode)

    // access log service configuration
    alsConfig := &als.HttpGrpcAccessLogConfig{
        CommonConfig: &als.CommonGrpcAccessLogConfig{
            LogName: "echo",
            GrpcService: &core.GrpcService{
                TargetSpecifier: &core.GrpcService_EnvoyGrpc_{
                    EnvoyGrpc: &core.GrpcService_EnvoyGrpc{
                        ClusterName: XdsCluster,
                    },
                },
            },
        },
    }
    alsConfigPbst, err := types.MarshalAny(alsConfig)
    if err != nil {
        panic(err)
    }

    // HTTP filter configuration
    manager := &hcm.HttpConnectionManager{
        CodecType:  hcm.AUTO,
        StatPrefix: "http",
        RouteSpecifier: &hcm.HttpConnectionManager_Rds{
            Rds: &hcm.Rds{
                ConfigSource:    rdsSource,
                RouteConfigName: route,
            },
        },
        HttpFilters: []*hcm.HttpFilter{{
            Name: util.Router,
        }},
        AccessLog: []*alf.AccessLog{{
            Name: util.HTTPGRPCAccessLog,
            ConfigType: &alf.AccessLog_TypedConfig{
                TypedConfig: alsConfigPbst,
            },
        }},
    }
    pbst, err := types.MarshalAny(manager)
    if err != nil {
        panic(err)
    }

    return &v2.Listener{
        Name: listenerName,
        Address: &core.Address{
            Address: &core.Address_SocketAddress{
                SocketAddress: &core.SocketAddress{
                    Protocol: core.TCP,
                    Address:  localhost,
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
