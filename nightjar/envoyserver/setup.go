package envoyserver

import (
	"net"
	"fmt"
	"google.golang.org/grpc"

	api "github.com/envoyproxy/go-control-plane/envoy/api/v2"
	discovery "github.com/envoyproxy/go-control-plane/envoy/service/discovery/v2"
	cache "github.com/envoyproxy/go-control-plane/pkg/cache"
	xds "github.com/envoyproxy/go-control-plane/pkg/server"
	core "github.com/envoyproxy/go-control-plane/envoy/api/v2/core"

	"github.com/groboclown/nightjar-mesh/nightjar/enviro"
	"github.com/groboclown/nightjar-mesh/nightjar/util"
)



type EnvoySvc struct {
	snapshotCache cache.SnapshotCache
	server *xds.Server
	grpcServer *grpc.Server
	port string

	Clusters, Endpoints, Routes, Listeners []cache.Resource
	Snapshot cache.Snapshot
}


func NewEnvoySvc(envoySetup *enviro.EnvoyRef, errorHandler func (error)) *EnvoySvc {
	snapshotCache := cache.NewSnapshotCache(false, idHash{}, nil)
	server := xds.NewServer(snapshotCache, nil)
	grpcServer := grpc.NewServer()

	discovery.RegisterAggregatedDiscoveryServiceServer(grpcServer, server)
	api.RegisterEndpointDiscoveryServiceServer(grpcServer, server)
	api.RegisterClusterDiscoveryServiceServer(grpcServer, server)
	api.RegisterRouteDiscoveryServiceServer(grpcServer, server)
	api.RegisterListenerDiscoveryServiceServer(grpcServer, server)

	svc := EnvoySvc{
		snapshotCache: snapshotCache,
		server: &server,
		grpcServer: grpcServer,
		port: getEnvoyPort(envoySetup),
	}
	svc.Snapshot = cache.NewSnapshot("1.0", svc.Endpoints, svc.Clusters, svc.Routes, svc.Listeners)

	return &svc
}


func (e *EnvoySvc) Run() {
	lis, _ := net.Listen("tcp", e.port)
	if err := e.grpcServer.Serve(lis); err != nil {
		util.Fatal("Failed to start server:", err)
	}
}


func getEnvoyPort(envoySetup *enviro.EnvoyRef) string {
	return fmt.Sprintf(":%d", envoySetup.AdminPort)
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
