package aws


import (
    //"github.com/aws/aws-sdk-go/aws"
    //"github.com/aws/aws-sdk-go/aws/awserr"
    "github.com/aws/aws-sdk-go/service/ecs"
    "github.com/groboclown/nightjar-mesh/nightjar/util"
)


func LoadTasks(ecsSvc *ecs.ECS, builders []*ServiceBuilder, cluster *string) ([]*AwsTaskPortInfo, error) {
    util.AssertNotNil(ecsSvc)
    util.AssertNotNil(cluster)

    util.Logf("Loading all tasks for cluster %s, %d builders", *cluster, len(builders))

    ret := make([]*AwsTaskPortInfo, 0)

    if len(builders) <= 0 {
        return ret, nil
    }

    taskArns := make([]*string, 0)

    tErr := ecsSvc.ListTasksPages(
        &ecs.ListTasksInput{
            Cluster: cluster,
            // DesiredStatus: "RUNNING",
        },
        func(output *ecs.ListTasksOutput, lastPage bool) bool {
            for _, taskArn := range output.TaskArns {
                util.Debug("Found task ARN", util.AsStr(taskArn))
                taskArns = append(taskArns, taskArn)
            }
            return true
        },
    )
    if tErr != nil {
        return ret, tErr
    }

    tErr = loop_over_tasks(
        ecsSvc, cluster, taskArns,
        func (task *ecs.Task) {
            // task can't be null, because of the loop check, and cluster should be right,
            // but we have the cluster name, and the task has the cluster arn.
            if (*task.LastStatus != "RUNNING") {
                util.Debugf("Task %s is not running", util.AsStr(task.TaskArn))
                return
            }
            
            if builder := find_builder_for_task(task, builders) ; builder != nil {
                var deploymentId *string = nil
                if taskDef := find_task_definition(task, builder) ; taskDef != nil {
                    deploymentId = taskDef.DeploymentId
                }
                util.Debugf("Task %s runs in %d containers.", util.AsStr(task.TaskArn), len(task.Containers))
                for _, container := range task.Containers {
                    // If there are no network bindings for the container, then we don't
                    // care about it.

                    util.Debugf("Container %s has %d network bindings.", util.AsStr(container.ContainerArn), len(container.NetworkBindings))
                    
                    for _, nb := range container.NetworkBindings {
                        util.Debugf(
                            "Found task %s, container %s, port %d, host port %d",
                            util.AsStr(task.TaskArn), util.AsStr(container.Name), util.AsInt64(nb.ContainerPort), util.AsInt64(nb.HostPort),
                        )
                        taskPortInfo := AwsTaskPortInfo{
                            RefId: nil,
                            ServiceArn: builder.ServiceArn,
                            ServiceName: builder.ServiceName,
                            ClusterName: builder.ClusterName,
                            ClusterArn: builder.ClusterArn,
                            TaskArn: task.TaskArn,
                            ContainerArn: container.ContainerArn,
                            ContainerName: container.Name,
                            DockerRuntimeId: container.RuntimeId,
                            ContainerInstanceArn: task.ContainerInstanceArn,
                            LaunchType: task.LaunchType,
                            TaskDefinitionArn: task.TaskDefinitionArn,
                            TaskDefinitionDeploymentId: deploymentId,
                            ContainerBindIp: nb.BindIP,
                            ContainerPort: nb.ContainerPort,
                            HostPort: nb.HostPort,
                            Protocol: nb.Protocol,
                        }
                        ret = append(ret, &taskPortInfo)
                    }
                }
            } else {
                util.Debugf("No known service associated with task %s", util.AsStr(task.TaskArn))
            }
        },
    )

    return ret, tErr
}


func loop_over_tasks(ecsSvc *ecs.ECS, cluster *string, taskArns []*string, fn func (*ecs.Task)) error {
    // Query at most 100 per shot.  It's the API limit.
    for i := 0 ; i < len(taskArns) ; {
        page := make([]*string, 0)
        for ; len(page) < 100 && i < len(taskArns) ; i += 1 {
            if taskArns[i] != nil {
                util.Debugf("getting task description for %s", *taskArns[i])
                page = append(page, taskArns[i])
            }
        }
        util.Debugf("Loading %d task descriptions from cluster %s", len(page), util.AsStr(cluster))
        output, lbErr := ecsSvc.DescribeTasks(
            &ecs.DescribeTasksInput{
                Cluster: cluster,
                Tasks: page,
            },
        )
        if lbErr != nil {
            return lbErr
        }
        util.Debugf("Load returned %d tasks", len(output.Tasks))
        for _, task := range output.Tasks {
            if task != nil {
                fn(task)
            }
        }
    }
    return nil
}


func find_task_definition(task *ecs.Task, builder *ServiceBuilder) *TaskDefinitionDeployment {
    if task == nil || builder == nil || task.TaskDefinitionArn == nil {
        return nil
    }
    return builder.TaskDefinitions[*task.TaskDefinitionArn]
}


func find_builder_for_task(task *ecs.Task, builders []*ServiceBuilder) *ServiceBuilder {
    if task == nil || task.TaskDefinitionArn == nil {
        return nil
    }
    for _, builder := range builders {
        if builder != nil && builder.TaskDefinitions[*task.TaskDefinitionArn] != nil {
            return builder
        }
    }
    return nil
}
