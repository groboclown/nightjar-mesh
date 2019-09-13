package envoy


// EnvoyAdminSvr interacts with the administration port on the envoy server.
// See https://www.envoyproxy.io/docs/envoy/latest/operations/admin
// See https://www.envoyproxy.io/docs/envoy/latest/configuration/operations/runtime#config-runtime-admin
type EnvoyAdminSvr interface {
	Clusters()  []*ClusterConfig
	SetClusters([]*ClusterConfig)

}

type ClusterConfig struct {
	Name		string
	DefaultPriority	*ClusterPriorityOptions
	HighPriority	*ClusterPriorityOptions
	Endpoints	[]*ClusterEndpoint
}

type ClusterEndpoint struct {
	Host		string
	Port		uint32
	Options		map[string]string
}

type ClusterPriorityOptions struct {
	MaxConnections	uint32
	MaxPendingRequests	uint32
	MaxRequests	uint32
	MaxRetries	uint32
}
