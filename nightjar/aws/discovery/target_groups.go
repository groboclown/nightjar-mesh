package discovery


// OLD CRUFT


import (
    //"github.com/aws/aws-sdk-go/aws"
    //"github.com/aws/aws-sdk-go/aws/awserr"
    "github.com/aws/aws-sdk-go/service/ecs"
    "github.com/aws/aws-sdk-go/service/elbv2"
)

/**
 * Get all the information for the services in the cluster, without digging deeper.
 *
 * For each valid, active service ARN, a builder is returned with the following
 * target group fields defined:
 *      serviceArn
 *      clusterArn
 *      clusterName
 *      targetGroups[]:
 *          targetGroupArn, loadBalancerName, containerPort, containerName,
 *      taskDefinitions[]:
 *          taskDefinitionArn, deploymentId, launchType,
 *      
 */
func load_services_for_cluster(ecsSvc *ecs.ECS, serviceArns []string, cluster string) ([]service_builder, error) {
    ret := make([]service_builder, len(serviceArns))

    // Pull the service description.
    // We can only do at most 10 per call.
    for i := 0 ; i < len(serviceArns) ; {
        serviceArnPtr := make([]*string, 0)
        for len(serviceArnPtr) < 10 && i < len(serviceArns) {
            serviceArnPtr = append(serviceArnPtr, &serviceArns[i])
            i++
        }
        servicesDesc, dsErr := ecsSvc.DescribeServices(
            &ecs.DescribeServicesInput{
                Cluster: &cluster,
                Services: serviceArnPtr,
            })
        if dsErr != nil {
            return ret, dsErr
        }

        // TODO extract below logic to allow for unit testing w/ mocked result data.

        // Load the top-level details for the services.
        for serviceDesc := servicesDesc.Services {
            if serviceDesc.Status != "ACTIVE" {
                // Value is DRAINING or INACTIVE
                // Don't use this service now.
                continue
            }
            builder := service_builder{
                targetGroups: make([]target_group, 0),
                taskDefinitions: make([]task_definition_deployment, 0),
                taskPorts: make([]task_container_port_info, 0)
                clusterName: cluster,
                clusterArn: serviceDesc.ClusterArn,
                launchType: serviceDesc.LaunchType,
                serviceArn: serviceDesc.ServiceArn,
                serviceName: serviceDesc.ServiceName,
            }
            
            for dep := range serviceDesc.Deployments {
                if dep.Status != "INACTIVE" {
                    // Value is ACTIVE or PRIMARY
                    td := task_definition_deployment{
                        taskDefinitionArn: dep.TaskDefinition,
                        deploymentId: dep.Id,
                        launchType: dep.LaunchType,
                    }
                    builder.taskDefinitions = append(bulder.taskDefinitions, td)
                }
            }
            for lb := range serviceDesc.LoadBalancers {
                if lb.TargetGroupArn != nil && tg.ContainerPort != nil {
                    tg := target_group{
                        targetGroupArn: lb.TargetGroupArn,
                        loadBalancerArn: nil,
                        loadBalancerName: lb.LoadBalancerName,
                        containerPort: lb.ContainerPort,
                        containerName: lb.ContainerName,
                        balancerPort: nil,
                        balancerDns: nil,
                        balancerProtocol: nil,
                        listenerArn: nil,
                    }
                    builder.targetGroups = append(builder.targetGroups, tg)
                }
            }
        }
    }

    return ret, nil
}


/**
 * Fills in these fields for each builder:
 *  targetGroups[]:
 *      balancerPort, balancerProtocol, loadBalancerArn,
 *
 */
func load_target_groups(elbSvc *elbv2.ELBV2, builders []service_builder) error {
    arns := make([]*string, 0)
    tg_map := make([string]*target_group)
    for builder := range builders {
        for tg := range builder.target_group {
            arns = append(arns, &tg.targetGroupArn)
            if _, ok := tg_map[tg.targetGroupArn] ; ok {
                panic("Duplicate target group arn; should not be encountered yet.")
            }
            tg_map[tg.targetGroupArn] = &tg
        }
    }

    tgErr := elbSvc.DescribeTargetGroupsPages(
        &elbv2.DescribeTargetGroupsInput{
            TargetGroupArns: arns,
        },
        func (output *DescribeTargetGroupsOutput, lastPage bool) bool {
            for group := range output.TargetGroups {
                
                if tg, ok := tg_map[group.TargetGroupArn] ; ok {
                    tg.balancerPort = group.Port
                    tg.balancerProtocol = group.Protocol

                    // If there is more than one load balancer associated with this
                    // target group, duplicate it.

                    if len(group.LoadBalancerArns) == 1 {
                        tg.loadBalancerArn = group.LoadBalancerArns[0]
                    }
                    // Note the starting index at 1...
                    for i := 1 ; i < len(group.LoadBalancerArns) ; i++ {
                        duplicate_target_group(&tg, group.LoadBalancerArns[i], builders)
                    }
                }
            }
            return true
        },
    )
    return tgErr
}


// Clones a target group with a different load balancer arn,
// and adds it into all services with that target group.
func duplicate_target_group(tg *target_group, loadBalancer *string, builders []service_builder) {
    for builder := range builders {
        newGroups := make([]target_group, len(builder.targetGroups) + 1)
        for btg := builder.targetGroups {
            newGroups = append(newGroups, btg)
            if btg.targetGroupArn == tg.targetGroupArn {
                dup := target_group{
                    loadBalancerArn: loadBalancer,  // the difference

                    targetGroupArn: tg.targetGroupArn,
                    loadBalancerName: tg.loadBalancerName,
                    containerPort: tg.containerPort,
                    containerName: tg.containerName,
                    balancerPort: tg.balancerPort,
                    balancerDns: tg.balancerDns,
                    balancerProtocol: tg.balancerProtocol,
                    hostedZoneId: tg.hostedZoneId,
                    vpcId: tg.vpcId,
                }
                newGroups = append(newGroups, dup)
            }
        }
        builder.targetGroups = newGroups
    }
}


/**
 * Loads the Application Load Balancer information for all services.
 *
 * Updates the builders with:
 *
 *   targetGroups[]:
 *      loadBalancerArn, balancerDns, hostedZoneId, vpcId, listenerArn,
 */
func load_elb(elbSvc *elbv2.ELBV2, builders []service_builder) error {
    // Gather up all the load balancers.
    balancers := make([]*string, len(builders))
    balancerTargets := make(map[string][]target_group)
    for builder := range builders {
        for tg := range builder.target_group {
            groups, ok := balancerTargets[tg.loadBalancerArn]
            if ! ok {
                groups = make([]target_group, 1)
                balancers = append(balancers, &tg.loadBalancerArn)
            }
            groups = append(groups, tg)
            balancerTargets[tg.loadBalancerArn] = groups
        }
    }

    lbErr := loop_over_load_balancers(
        elbSvc, balancers,
        func (lb *elbv2.LoadBalancer) {
            if groups, ok := balancerTargets[lb.loadBalancerArn] ; ok {
                for tg := range groups {
                    tg.loadBalancerArn = lb.LoadBalancerArn
                    tg.balancerDns = lb.DNSName
                    tg.hostedZoneId = lb.CanonicalHostedZoneId
                    tg.vpcId = lb.VpcId
                }
            }
        },
    )
    if lbErr != nil {
        return lbErr
    }

    // This requires an extra call for every load balancer, but has no gain.
    // for balancerArn, groups := balancerTargets {
    //     lnErr := elbSvc.DescribeListenersPages(
    //         &DescribeListenersInput{ LoadBalancerArn: &balancerArn },
    //         func (output *DescribeListenersOutput, lastPage bool) bool {
    //             for listener := output.Listeners {
    //                 for group := range groups {
    //                     if *(group.balancerPort) == *(listener.Port) {
    //                         group.listenerArn = listener.ListenerArn
    //                     }
    //                 }
    //             }
    //             return true
    //         }
    //     )
    //     if lnErr != nil {
    //         return lnErr
    //     }
    // }

    return nil
}


func loop_over_load_balancers(elbSvc *elbv2.ELBV2, balancerArns []*string, fn func (*LoadBalancer)) error {
    func paged(output *elbv2.DescribeLoadBalancersOutput, lastPage bool) bool {
        if output != nil {
            for lb := range output.LoadBalancers {
                if lb != nil {
                    fn(lb)
                }
            }
        }
        return true
    }

    // Query at most 20 per shot.  It's the API limit.
    for i := 0 ; i < len(balancerArns) ; {
        page := make([]*string, 20)
        for ; len(page) < 20 && i < len(balancerArns) ; i += 1 {
            page = append(page, balancerArns[i])
        }
        lbErr := elbSvc.DescribeLoadBalancersPages(
            &elbv2.DescribeLoadBalancersInput{
                LoadBalancerArns: page,
            },
            paged,
        )
        if lbErr != nil {
            return lbErr
        }
    }
    return nil
}


func load_tasks(ecsSvc *ecs.ECS, builders []service_builder) error {
    tasks := make(map[string]*service_builder)
    taskArns := make([]*string, len(builders))
    cluster := builders[0].cluster  // BUG?!?
    for builder := range builders {
        tErr := ecsSvc.ListTasksPages(
            &ecs.ListTasksInput{
                Cluster: &builder.cluster,
                DesiredStatus: &"RUNNING",
                // supposedly optional, but it's not.
                ServiceName: builder.serviceName,
            },
            func(output *ListTasksOutput, lastPage bool) bool {
                for taskArn := range output.TaskArns {
                    tasks[taskArn] = &builder
                    taskArns = append(taskArns, taskArn)
                }
                return true
            }
        )
        if tErr != nil {
            return tErr
        }
    }

    tErr := loop_over_tasks(
        ecsSvc, cluster, taskArns,
        func (task *ecs.Task) {
            if service, ok := tasks[task.TaskArn] ; ok {
                for container := range task.Containers {
                    // If there are no network bindings for the container, then we don't
                    // care about it.
                    for nb := range container.NetworkBindings {
                        taskPortInfo := task_container_port_info{
                            taskArn: task.TaskArn,
                            containerArn: container.ContainerArn,
                            containerName: container.Name,
                            dockerRuntimeId: container.RuntimeId,
                            containerInstanceArn: task.ContainerInstanceArn,
                            launchType: task.LaunchType,
                            taskDefinitionArn: task.TaskDefinitionArn,
                            containerBoundIp: nb.BindIP,
                            containerPort: nb.ContainerPort,
                            hostPort: nb.HostPort,
                            protocol: nb.Protocol,
                        }
                        service.taskPorts = append(service.taskPorts, taskPortInfo)
                    }
                }
            }
        },
    )

    return nil
}


func loop_over_tasks(ecsSvc *ecs.ECS, cluster string, taskArns []*string, fn func (*ecs.Task)) error {
    // Query at most 100 per shot.  It's the API limit.
    for i := 0 ; i < len(taskArns) ; {
        page := make([]*string, 100)
        for ; len(page) < 100 && i < len(taskArns) ; i += 1 {
            page = append(page, taskArns[i])
        }
        output, lbErr := ecsSvc.DescribeTasks(
            &ecs.DescribeTasksInput{
                Cluster: 
                Tasks: page,
            },
            paged,
        )
        if lbErr != nil {
            return lbErr
        }
        for task := range output.Tasks {
            if task != nil {
                fn(task)
            }
        }
    }
    return nil
}
