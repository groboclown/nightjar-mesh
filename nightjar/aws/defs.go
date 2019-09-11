package aws


// ==========================================================================
// Public Types

/**
 * Detailed information about an AWS ECS container's port.
 *
 * If the container is not assigned a load balancer, then the
 * AlbPort will equal the ContainerPort, and the DnsName will
 * be the ContainerHost.
 */
type AwsTaskPortInfo struct {
    RefId                       *string
    ProxyPath                   *string

    ServiceArn                  *string
    ServiceName                 *string
    ClusterName                 *string
    ClusterArn                  *string

    TaskArn                     *string
    ContainerArn                *string
    ContainerName               *string
    DockerRuntimeId             *string
    ContainerInstanceArn        *string
    LaunchType                  *string
    TaskDefinitionArn           *string
    TaskDefinitionDeploymentId  *string
    ContainerBindIp             *string
    ContainerPort               *int64
    HostPort                    *int64
    Protocol                    *string
}


type AwsTaskPortInfoDiffs struct {
    Removed      []*AwsTaskPortInfo
    Added        []*AwsTaskPortInfo
}
