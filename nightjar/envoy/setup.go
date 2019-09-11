package envoy

import (
    "strings"
    "strconv"
    "net"
    "google.golang.org/grpc"

    api "github.com/envoyproxy/go-control-plane/envoy/api/v2"
    discovery "github.com/envoyproxy/go-control-plane/envoy/service/discovery/v2"
    cache "github.com/envoyproxy/go-control-plane/pkg/cache"
    xds "github.com/envoyproxy/go-control-plane/pkg/server"
    core "github.com/envoyproxy/go-control-plane/envoy/api/v2/core"

    "github.com/groboclown/nightjar-mesh/nightjar/enviro"
)



type EnvoySvc struct {
    SnapshotCache cache.SnapshotCache
    Server *xds.Server
    GrpcServer *grpc.Server

    Clusters, Endpoints, Routes, Listeners []cache.Resource
    Snapshot cache.Snapshot
}


func NewEnvoySvc(envoySetup *enviro.EnvoyRef, errorHandler func (error)) *EnvoySvc {
    snapshotCache := cache.NewSnapshotCache(false, idHash{}, nil)
    server := xds.NewServer(snapshotCache, nil)
    grpcServer := grpc.NewServer()
    lis, _ := net.Listen("tcp", getEnvoyPort(envoySetup))

    discovery.RegisterAggregatedDiscoveryServiceServer(grpcServer, server)
    api.RegisterEndpointDiscoveryServiceServer(grpcServer, server)
    api.RegisterClusterDiscoveryServiceServer(grpcServer, server)
    api.RegisterRouteDiscoveryServiceServer(grpcServer, server)
    api.RegisterListenerDiscoveryServiceServer(grpcServer, server)
    go func() {
        if err := grpcServer.Serve(lis); err != nil {
            errorHandler(err)
        }
    }()

    svc := EnvoySvc{
        SnapshotCache: snapshotCache,
        Server: &server,
        GrpcServer: grpcServer,
    }
    svc.Snapshot = cache.NewSnapshot("1.0", svc.Endpoints, svc.Clusters, svc.Routes, svc.Listeners)

    return &svc
}


func getEnvoyPort(envoySetup *enviro.EnvoyRef) string {
    return strings.Join([]string{
        envoySetup.Hostname,
        strconv.FormatInt(envoySetup.Port, 10),
    }, ":")
}


// Should use this from cache.IDHash, but that's not imported right.
// Why?
// IDHash uses ID field as the node hash.
type idHash struct{}

// ID uses the node ID field
func (idHash) ID(node *core.Node) string {
	if node == nil {
		return ""
	}
	return node.Id
}
