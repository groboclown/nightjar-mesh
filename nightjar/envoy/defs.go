package envoy


type ServiceEndpoint {
	HostIP		string
    HostPort    uint32
}

type ServceCluster {
    ServiceName string
    Paths       []string
    Endpoints   []ServiceEndpoint
    Http1Only   bool
}
