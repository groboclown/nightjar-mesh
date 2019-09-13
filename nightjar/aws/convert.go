package aws


import (
	"github.com/groboclown/nightjar-mesh/nightjar/enviro"
	"github.com/groboclown/nightjar-mesh/nightjar/util"
)


/**
 * Returns (egress, ingress, err)
 */
func DiscoverInOutTasks(svc *AwsSvc, egressList []*enviro.PathRef, ingressList []*enviro.PathRef) ([]*AwsTaskPortInfo, []*AwsTaskPortInfo, error) {
	serviceArnsByCluster := collectServiceClusters(egressList, ingressList)

	retOut := make([]*AwsTaskPortInfo, 0)
	retIn := make([]*AwsTaskPortInfo, 0)
	for cluster, serviceArns := range *serviceArnsByCluster {
		taskPorts, err := DiscoverServiceDetails(svc, serviceArns, &cluster)
		if err != nil {
			return retOut, retIn, err
		}
		for _, egress := range egressList {
			retOut = append(retOut, findMatches(egress, taskPorts)...)
		}
		for _, ingress := range ingressList {
			retIn = append(retIn, filterNonLocal(findMatches(ingress, taskPorts), svc.LocalIp)...)
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
					serviceList = make([]*string, 0)
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
	matches := make([]*AwsTaskPortInfo, 0)
	var usingPort uint32 = 0
	var usingContainerName *string = nil

	for _, taskPort := range taskPorts {
		if (
				*pathRef.ServiceArn != *taskPort.ServiceArn ||
				*pathRef.Cluster != *taskPort.ClusterName ||

				// Special check considerations...
				(pathRef.ContainerName != nil && *pathRef.ContainerName != *taskPort.ContainerName) ||
				(pathRef.ContainerPort > 0 && pathRef.ContainerPort != taskPort.ContainerPort)) {
			continue
		}

		if (
				(pathRef.ContainerPort <= 0 && usingPort >= 0 && usingPort != taskPort.ContainerPort) ||
				(pathRef.ContainerName == nil && usingContainerName != nil && *usingContainerName != *taskPort.ContainerName)) {
			if notDisplayedErrorHeader {
				notDisplayedErrorHeader = false
				util.Warn(" Discovered multiple conflicting matches")
				util.Warn("   Requested task:")
				util.Warn("          Cluster: %s", pathRef.Cluster)
				util.Warn("      Service ARN: %s", pathRef.ServiceArn)
				if pathRef.ContainerName == nil {
					util.Warn("        Container: (not given)")
				} else {
					util.Warn("        Container: %s", pathRef.ContainerName)
				}
				if pathRef.ContainerPort < 0 {
					util.Warn("  Constainer Port: (not given)")
				} else {
					util.Warn("  Constainer Port: %d", pathRef.ContainerPort)
				}
				// Show the already matched ones.
				for _, match := range matches {
					displayMatch(match)
				}
			}
			displayMatch(taskPort)
		} else {
			usingPort = taskPort.ContainerPort
			usingContainerName = taskPort.ContainerName
			taskPort.RefId = &pathRef.Id
			taskPort.ProxyPath = pathRef.Path
			matches = append(matches, taskPort)
		}
	}
	return matches
}


func displayMatch(taskPort *AwsTaskPortInfo) {
	util.Warn("        Matched Against:")
	util.Warn(" -----------------------")
	// Always the same, so don't show:
	//   ServiceName, ClusterArn
	// Don't need to show?
	//   ContainerArn, DockerRuntimeId, ContainerInstanceArn, LaunchType
	//   TaskDefinitionArn, TaskDefinitionDeploymentId, ContainerBindIp, HostPort
	util.Warn("               Task ARN: %s", taskPort.TaskArn)
	// util.Warn("          Container ARN: %s", taskPort.ContainerArn)
	util.Warn("         Container Name: %s", taskPort.ContainerName)
	util.Warn("         Container Port: %s %d", *taskPort.Protocol, taskPort.ContainerPort)
}


/**
 * Filter out all the task ports which do not reference a service running on the
 * current computer.
 */
func filterNonLocal(taskPorts []*AwsTaskPortInfo, localIp string) []*AwsTaskPortInfo {
	ret := make([]*AwsTaskPortInfo, len(taskPorts))

	for _, taskPort := range taskPorts {
		if *taskPort.Ec2InstancePrivateIp == localIp {
			ret = append(ret, taskPort)
		}
	}

	return ret
}
