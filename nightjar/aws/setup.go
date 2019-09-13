package aws

import (
	"log"
	//"github.com/aws/aws-sdk-go/aws"
	//"github.com/aws/aws-sdk-go/aws/awserr"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/ec2"
	"github.com/aws/aws-sdk-go/service/ecs"
	//"github.com/aws/aws-sdk-go/service/elbv2"
)


type AwsSvc struct {
	ecs		*ecs.ECS
	ec2     *ec2.EC2
	LocalIp string

	// There are a lot of opportunities to cache the gathered data.
	// Each resource requested will have a unique ARN that, for everything
	// except the status parts, will be the same.

	// Options for caching:
	// - ec2:DescribeInstances
	//      These can be completely cached.  Information
	//      pulled from here is the network address, which only
	//      changes when the ec2 instance changes.
	//      The ec2 instance list is completely defined through
	//      the containers, so only the unknown instances need
	//      to be fetched, and unused instances can be flushed
	//      from the cache.
	// - ecs:DescribeContainerInstances
	//      Container instances change when the list of
	//      tasks change, otherwise the values remain the
	//      same.  The only item that changes in this list
	//      that we care about is the container status.
	// - ecs:DescribeServices
	//      The list of services is static.  The data returned
	//      by this call will remain the same for the same service
	//      ARN.  This call can be fetched just once and kept
	//      forever.
	// - ecs:ListTasks
	//      The list of active tasks can change all the time, due to
	//      the flexibility with ECS.  Due to that, this list cannot
	//      be cached.
	// - ecs:DescribeTasks
	//      The list of containers can change and the number of instances
	//      fluxuates, even though each container itself is mostly static.
	//      This shouldn't be cached.
}


func NewAwsSvc(failIfNotEc2 bool) *AwsSvc {
	sess := session.Must(session.NewSession())
	ecsSvc := ecs.New(sess)
	ec2Svc := ec2.New(sess)
	// any other services we may want...

	localIp, lErr := GetInstanceIp()
	if lErr != nil {
		if failIfNotEc2 {
			log.Fatalln("Could not find local IP; Perhaps this computer is not an ECS instance?  Error:", lErr)
		}
		localIp = "(unknown)"
	}

	return &AwsSvc{
		ecs: ecsSvc,
		ec2: ec2Svc,
		LocalIp: localIp,
	}
}
