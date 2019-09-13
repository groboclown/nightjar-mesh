package envoy


type ServiceEndpoint struct {
	HostIP		string
	HostPort    uint32
}

type ServiceCluster struct {
	ServiceName string
	Paths       []string
	Endpoints   []ServiceEndpoint
	Http1Only   bool
}
