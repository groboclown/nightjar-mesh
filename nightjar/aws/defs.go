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
	ContainerPort               uint32
	HostPort                    uint32
	Protocol                    *string

	// Populated separately in the "container.go" file.
	Ec2InstanceId               *string
	Ec2InstancePublicDns        *string
	Ec2InstancePublicIp         *string
	Ec2InstancePrivateDns       *string
	Ec2InstancePrivateIp        *string
	Ec2InstanceSubnetId         *string
}


type AwsTaskPortInfoDiffs struct {
	Removed      []*AwsTaskPortInfo
	Added        []*AwsTaskPortInfo
}
