package aws


import (
    //"github.com/aws/aws-sdk-go/aws"
    //"github.com/aws/aws-sdk-go/aws/awserr"
    "github.com/aws/aws-sdk-go/service/ecs"
    "github.com/groboclown/nightjar-mesh/nightjar/util"
)

/**
 * Get all the information for the services in the cluster, without digging deeper.
 *
 * For each valid, active service ARN, a builder is returned.  No TaskPorts are loaded.
 */
func LoadServicesForCluster(ecsSvc *ecs.ECS, serviceArns []*string, cluster *string) ([]*ServiceBuilder, error) {
    util.AssertNotNil(ecsSvc)
    util.AssertNotNil(cluster)

    ret := make([]*ServiceBuilder, len(serviceArns))

    // Pull the service description.
    // We can only do at most 10 per call.
    for i := 0 ; i < len(serviceArns) ; {
        serviceArnPtr := make([]*string, 0)
        for len(serviceArnPtr) < 10 && i < len(serviceArns) {
            serviceArnPtr = append(serviceArnPtr, serviceArns[i])
            i++
        }
        servicesDesc, dsErr := ecsSvc.DescribeServices(
            &ecs.DescribeServicesInput{
                Cluster: cluster,
                Services: serviceArnPtr,
            })
        if dsErr != nil {
            return ret, dsErr
        }

        // Load the top-level details for the services.
        for _, serviceDesc := range servicesDesc.Services {
            if service := CreateServiceFromServiceDescription(serviceDesc, cluster) ; service != nil {
                ret = append(ret, service)
            }
        }
    }

    return ret, nil
}


/**
 * private-but-testable function.
 */
func CreateServiceFromServiceDescription(serviceDesc *ecs.Service, cluster *string) *ServiceBuilder {
    if serviceDesc == nil || serviceDesc.Status == nil || *serviceDesc.Status != "ACTIVE" {
        // Value is DRAINING or INACTIVE
        // Don't use this service now.
        return nil
    }

    builder := ServiceBuilder{
        TaskDefinitions: make(map[string]*TaskDefinitionDeployment),
        ServiceArn: serviceDesc.ServiceArn,
        ServiceName: serviceDesc.ServiceName,
        ClusterName: cluster,
        ClusterArn: serviceDesc.ClusterArn,
        LaunchType: serviceDesc.LaunchType,
    }
    
    for _, dep := range serviceDesc.Deployments {
        if dep.Status != nil && *dep.Status != "INACTIVE" {
            // Value is ACTIVE or PRIMARY
            if dep.TaskDefinition != nil && dep.Id != nil {
                util.AssertNil(builder.TaskDefinitions[*dep.TaskDefinition])
                td := TaskDefinitionDeployment{
                    TaskDefinitionArn: dep.TaskDefinition,
                    DeploymentId: dep.Id,
                    LaunchType: dep.LaunchType,
                }
                builder.TaskDefinitions[*dep.TaskDefinition] = &td
            }
        }
    }

    // Ignore load balancers.
    //for _, lb := range serviceDesc.LoadBalancers {
    //    if lb.TargetGroupArn != nil && tg.ContainerPort != nil {
    //        tg := target_group{
    //            targetGroupArn: lb.TargetGroupArn,
    //            loadBalancerArn: nil,
    //            loadBalancerName: lb.LoadBalancerName,
    //            containerPort: lb.ContainerPort,
    //            containerName: lb.ContainerName,
    //            balancerPort: nil,
    //            balancerDns: nil,
    //            balancerProtocol: nil,
    //            listenerArn: nil,
    //        }
    //        builder.targetGroups = append(builder.targetGroups, tg)
    //    }
    //}

    return &builder
}
