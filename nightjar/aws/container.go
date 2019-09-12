package aws

import (
    //"github.com/aws/aws-sdk-go/aws"
    //"github.com/aws/aws-sdk-go/aws/awserr"
    "github.com/aws/aws-sdk-go/service/ecs"
    "github.com/aws/aws-sdk-go/service/ec2"
    "github.com/groboclown/nightjar-mesh/nightjar/util"
)


func PopulateContainerInstances(svc *AwsSvc, taskPorts []*AwsTaskPortInfo) error {
	// Gather up all the container instance arns.
	// From those, query for the container instances.
	// From those, query for all the EC2 instances,
	// from which we can populate the tasks.

	util.Logf("Associating %d tasks with their EC2 instances.", len(taskPorts))

	containersByCluster := getContainersByCluster(taskPorts)
	
	containerArnToEc2InstanceId := make(map[string]*string)
	for cluster, containers := range containersByCluster {
		err := findEc2InstanceIdsByContainerInstanceArn(svc.ecs, &cluster, containers, containerArnToEc2InstanceId)
		if err != nil {
			return err
		}
	}
	containerInstanceArnToEc2Instance, err := describeEc2InstancesByContainerInstanceArn(svc.ec2, containerArnToEc2InstanceId)
	if err != nil {
		return err
	}
	for containerInstanceArn, instance := range containerInstanceArnToEc2Instance {
		if instance == nil {
			continue
		}

		for _, taskPort := range taskPorts {
			util.Debugf("Checking %s against task %s container %s", containerInstanceArn, util.AsStr(taskPort.TaskArn), util.AsStr(taskPort.ContainerInstanceArn))
			if containerInstanceArn == *taskPort.ContainerInstanceArn {
				util.Debugf(
					"Associated task %s with EC2 instance ID %s (IP %s)",
					util.AsStr(taskPort.TaskArn),
					util.AsStr(instance.InstanceId),
					util.AsStr(instance.PrivateIpAddress),
				)
				taskPort.Ec2InstanceId = instance.InstanceId
				taskPort.Ec2InstancePublicDns = instance.PublicDnsName
				taskPort.Ec2InstancePublicIp = instance.PublicIpAddress
				taskPort.Ec2InstancePrivateDns = instance.PrivateDnsName
				taskPort.Ec2InstancePrivateIp = instance.PrivateIpAddress
				taskPort.Ec2InstanceSubnetId = instance.SubnetId
			}
		}
	}

	return nil
}


func getContainersByCluster(taskPorts []*AwsTaskPortInfo) map[string][]*string {
	containersByCluster := make(map[string][]*string)
	foundInstances := make(map[string]bool)
	for _, taskPort := range taskPorts {
		containers, ok := containersByCluster[*taskPort.ClusterName]
		if ! ok {
			containers = make([]*string, 0)
		}
		if _, iok := foundInstances[*taskPort.ContainerInstanceArn] ; ! iok {
			foundInstances[*taskPort.ContainerInstanceArn] = true
			containersByCluster[*taskPort.ClusterName] = append(containers, taskPort.ContainerInstanceArn)
		}
	}
	return containersByCluster
}


func findEc2InstanceIdsByContainerInstanceArn(
	ecsSvr *ecs.ECS,
	cluster *string,
	containerInstances []*string,
	ret map[string]*string,
) error {
	// Up to 100 can be queried at a time.
	for i := 0 ; i < len(containerInstances) ; {
		arns := make([]*string, 0)
		for len(arns) < 100 && i < len(containerInstances) {
			arns = append(arns, containerInstances[i])
			i++
		}

		util.Debugf("Describing %d containers", len(arns))
		output, err := ecsSvr.DescribeContainerInstances(&ecs.DescribeContainerInstancesInput{
			Cluster: cluster,
			ContainerInstances: arns,
		})

		if err != nil || output == nil {
			return err
		}

		for _, instance := range output.ContainerInstances {
			if instance.Ec2InstanceId != nil {
				// TODO ensure the container isn't already associated in the map.
				ret[*instance.ContainerInstanceArn] = instance.Ec2InstanceId
			}
		}
	}

	return nil
}


/**
 * Returns containerArn -> ec2.Instance.
 */
func describeEc2InstancesByContainerInstanceArn(
	ec2Svr *ec2.EC2,
	containerInstanceArnToEc2InstanceId map[string]*string,
) (map[string]*ec2.Instance, error) {
	ret := make(map[string]*ec2.Instance)

	// There doesn't seem to be a maximum for the number of instance IDs that can be
	// queried at a time.  However, to keep things sane, we'll limit the query to
	// 20 at a time.

	// Making a reverse map of container -> instance will mean we'll need multiple
	// values in the map.  So, instead we'll just search the whole list linearly
	// at the end, which isn't a big deal because the number of containers is small.

	ec2InstanceIds := make([]*string, 0)
	for _, ec2InstanceId := range containerInstanceArnToEc2InstanceId {
		// TODO eliminate duplicates from the list.
		ec2InstanceIds = append(ec2InstanceIds, ec2InstanceId)
	}

	for i := 0 ; i < len(ec2InstanceIds) ; {
		ids := make([]*string, 0)
		for len(ids) < 20 && i < len(ec2InstanceIds) {
			util.Debugf("getting description for ec2 instance %s", util.AsStr(ec2InstanceIds[i]))
			if ec2InstanceIds[i] != nil {
				ids = append(ids, ec2InstanceIds[i])
			}
			i++
		}

		util.Debugf("Describing %d ec2 instances", len(ids))
		output, err := ec2Svr.DescribeInstances(&ec2.DescribeInstancesInput{
			InstanceIds: ids,
		})

		if err != nil || output == nil {
			return ret, err
		}

		for _, res := range output.Reservations {
			for _, inst := range res.Instances {
				util.Debugf("matching up fetched instance %s", util.AsStr(inst.InstanceId))
				for containerArn, ec2InstanceId := range containerInstanceArnToEc2InstanceId {
					if *ec2InstanceId == *inst.InstanceId {
						util.Debugf("- matched against container %s", containerArn)
						ret[containerArn] = inst
					}
				}
			}
		}
	}

	return ret, nil
}
