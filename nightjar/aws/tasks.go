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

    ret := make([]*AwsTaskPortInfo, len(builders))

    if len(builders) <= 0 {
        return ret, nil
    }

    tasks := make(map[string]*ServiceBuilder)
    taskArns := make([]*string, len(builders))
    status := "RUNNING"
    for _, builder := range builders {
        tErr := ecsSvc.ListTasksPages(
            &ecs.ListTasksInput{
                Cluster: builder.ClusterName,
                DesiredStatus: &status,
                // Supposedly optional, but it's not.
                // Otherwise we could pull all of them down at once.
                ServiceName: builder.ServiceName,
            },
            func(output *ecs.ListTasksOutput, lastPage bool) bool {
                for _, taskArn := range output.TaskArns {
                    tasks[*taskArn] = builder
                    taskArns = append(taskArns, taskArn)
                }
                return true
            },
        )
        if tErr != nil {
            return ret, tErr
        }
    }

    tErr := loop_over_tasks(
        ecsSvc, cluster, taskArns,
        func (task *ecs.Task) {
            if service, ok := tasks[*task.TaskArn] ; ok {
                var deploymentId *string = nil
                if taskDef := find_task_definition(task, service) ; taskDef != nil {
                    deploymentId = taskDef.DeploymentId
                }
                for _, container := range task.Containers {
                    // If there are no network bindings for the container, then we don't
                    // care about it.
                    
                    for _, nb := range container.NetworkBindings {
                        taskPortInfo := AwsTaskPortInfo{
                            RefId: nil,
                            ServiceArn: service.ServiceArn,
                            ServiceName: service.ServiceName,
                            ClusterName: service.ClusterName,
                            ClusterArn: service.ClusterArn,
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
            }
        },
    )

    return ret, tErr
}


func loop_over_tasks(ecsSvc *ecs.ECS, cluster *string, taskArns []*string, fn func (*ecs.Task)) error {
    // Query at most 100 per shot.  It's the API limit.
    for i := 0 ; i < len(taskArns) ; {
        page := make([]*string, 100)
        for ; len(page) < 100 && i < len(taskArns) ; i += 1 {
            page = append(page, taskArns[i])
        }
        output, lbErr := ecsSvc.DescribeTasks(
            &ecs.DescribeTasksInput{
                Cluster: cluster,
                Tasks: page,
            },
        )
        if lbErr != nil {
            return lbErr
        }
        for _, task := range output.Tasks {
            if task != nil {
                fn(task)
            }
        }
    }
    return nil
}


func find_task_definition(task *ecs.Task, service *ServiceBuilder) *TaskDefinitionDeployment {
    if task == nil || service == nil || task.TaskDefinitionArn == nil {
        return nil
    }
    return service.TaskDefinitions[*task.TaskDefinitionArn]
}
