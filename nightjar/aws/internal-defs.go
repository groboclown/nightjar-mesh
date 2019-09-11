package aws

/**
 * Exploded data structures, populated from across the various AWS services.
 */
type ServiceBuilder struct {
    // Temporary data: map of the task definition ARN -> deployment data.
    TaskDefinitions map[string]*TaskDefinitionDeployment
    ServiceArn      *string
    ServiceName     *string
    ClusterName     *string
    ClusterArn      *string
    LaunchType      *string
}


// A temporary structure, used to populate the ports.
type TaskDefinitionDeployment struct {
    TaskDefinitionArn   *string
    DeploymentId        *string
    LaunchType          *string
}
