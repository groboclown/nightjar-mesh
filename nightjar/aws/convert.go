package aws

import (
    "fmt"
    "github.com/groboclown/nightjar-mesh/nightjar/enviro"
)


/**
 * Returns (egress, ingress, err)
 */
func DiscoverInOutTasks(svc *AwsSvc, egressList []*enviro.PathRef, ingressList []*enviro.PathRef) ([]*AwsTaskPortInfo, []*AwsTaskPortInfo, error) {
    serviceArnsByCluster := collectServiceClusters(egressList, ingressList)

    retOut := make([]*AwsTaskPortInfo, 1)
    retIn := make([]*AwsTaskPortInfo, 1)
    for cluster, serviceArns := range *serviceArnsByCluster {
        taskPorts, err := DiscoverServiceDetails(svc, serviceArns, &cluster)
        if err != nil {
            return retOut, retIn, err
        }
        for _, egress := range egressList {
            retOut = append(retOut, findMatches(egress, taskPorts)...)
        }
        for _, ingress := range ingressList {
            retIn = append(retIn, findMatches(ingress, taskPorts)...)
        }
    }

    return retOut, retIn, nil
}


func collectServiceClusters(lists ...[]*enviro.PathRef) *map[string][]*string {
    serviceArnsByCluster := make(map[string][]*string)
    for _, pr := range lists {
        for _, pathRef := range pr {
            if pathRef.ServiceArn != nil && pathRef.Cluster != nil {
                serviceList, ok := serviceArnsByCluster[*(pathRef.Cluster)]
                if ! ok {
                    serviceList = make([]*string, 2)
                }
                serviceArnsByCluster[*(pathRef.Cluster)] = append(serviceList, pathRef.ServiceArn)
            }
        }
    }
    return &serviceArnsByCluster
}


func findMatches(pathRef *enviro.PathRef, taskPorts []*AwsTaskPortInfo) []*AwsTaskPortInfo {
    // if the pathRef.ContainerPort < 0, don't match on the port; but if there are
    // more than one task port match, then it's an error.
    // Likewise with the ContainerName, if it's nil, then ignore it unless there are
    // multiple matches.

    // It can match against multiple deployments, though.

    notDisplayedErrorHeader := true
    matches := make([]*AwsTaskPortInfo, 1)
    var usingPort int64 = -1
    var usingContainerName *string = nil

    for _, taskPort := range taskPorts {
        if (
                *pathRef.ServiceArn != *taskPort.ServiceArn ||
                *pathRef.Cluster != *taskPort.ClusterName ||

                // Special check considerations...
                (pathRef.ContainerName != nil && *pathRef.ContainerName != *taskPort.ContainerName) ||
                (pathRef.ContainerPort >= 0 && pathRef.ContainerPort != *taskPort.ContainerPort)) {
            continue
        }

        if (
                (pathRef.ContainerPort < 0 && usingPort >= 0 && usingPort != *taskPort.ContainerPort) ||
                (pathRef.ContainerName == nil && usingContainerName != nil && *usingContainerName != *taskPort.ContainerName)) {
            if notDisplayedErrorHeader {
                notDisplayedErrorHeader = false
                fmt.Printf("[ERROR] Discovered multiple conflicting matches")
                fmt.Printf("        Requested task:")
                fmt.Printf("           Cluster: %s", pathRef.Cluster)
                fmt.Printf("       Service ARN: %s", pathRef.ServiceArn)
                if pathRef.ContainerName == nil {
                    fmt.Printf("         Container: (not given)")
                } else {
                    fmt.Printf("         Container: %s", pathRef.ContainerName)
                }
                if pathRef.ContainerPort < 0 {
                    fmt.Printf("              Constainer Port: (not given)")
                    } else {
                    fmt.Printf("              Constainer Port: %d", pathRef.ContainerPort)
                }
                // Show the already matched ones.
                for _, match := range matches {
                    displayMatch(match)
                }
            }
            displayMatch(taskPort)
        } else {
            usingPort = *taskPort.ContainerPort
            usingContainerName = taskPort.ContainerName
            taskPort.RefId = &pathRef.Id
            taskPort.ProxyPath = pathRef.Path
            matches = append(matches, taskPort)
        }
    }
    return matches
}


func displayMatch(taskPort *AwsTaskPortInfo) {
    fmt.Printf("        Matched Against:")
    fmt.Printf(" -----------------------")
    // Always the same, so don't show:
    //   ServiceName, ClusterArn
    // Don't need to show?
    //   ContainerArn, DockerRuntimeId, ContainerInstanceArn, LaunchType
    //   TaskDefinitionArn, TaskDefinitionDeploymentId, ContainerBindIp, HostPort
    fmt.Printf("               Task ARN: %s", taskPort.TaskArn)
    // fmt.Printf("          Container ARN: %s", taskPort.ContainerArn)
    fmt.Printf("         Container Name: %s", taskPort.ContainerName)
    fmt.Printf("         Container Port: %s %d", *taskPort.Protocol, *taskPort.ContainerPort)
}
