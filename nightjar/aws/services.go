package aws


import (
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

    ret := make([]*ServiceBuilder, 0)

    // Pull the service description.
    // We can only do at most 10 per call.
    util.Logf("Loading %d services for cluster %s", len(serviceArns), *cluster)
    for i := 0 ; i < len(serviceArns) ; {
        serviceArnPtr := make([]*string, 0)
        for len(serviceArnPtr) < 10 && i < len(serviceArns) {
            if serviceArns[i] != nil {
                serviceArnPtr = append(serviceArnPtr, serviceArns[i])
                util.Debugf("With service ARN %s", *serviceArns[i])
            } else {
                util.Debugf("Encountered nil service ARN at index %d.", i)
            }
            i++
        }
        servicesDesc, dsErr := ecsSvc.DescribeServices(
            &ecs.DescribeServicesInput{
                Cluster: cluster,
                Services: serviceArnPtr,
            })
        if dsErr != nil {
            util.Log("Describe Services generated error:", dsErr)
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
                util.Debugf("Parsing task definition %s; deployment ID %s; launch type %s", *dep.TaskDefinition, *dep.Id, *dep.LaunchType)
                if _, ok := (builder.TaskDefinitions[*dep.TaskDefinition]) ; ok {
                    util.Errorf("Expected only one task definition %s, but found multiples.", *dep.TaskDefinition)
                }
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
