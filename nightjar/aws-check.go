package nightjar

import (
    "fmt"

    "github.com/groboclown/nightjar-mesh/nightjar/enviro"
    "github.com/groboclown/nightjar-mesh/nightjar/aws"
    "github.com/groboclown/nightjar-mesh/nightjar/util"
)


func AwsCheck() {
    awsSvc := aws.NewAwsSvc(false)
    egressDef := enviro.ReadEgress()
	ingressDef := enviro.ReadIngress()
	
	fmt.Printf("Local AWS IP: %s\n", awsSvc.LocalIp)

	util.Debug("Loading AWS services...")
	egress, ingress, err := aws.DiscoverInOutTasks(awsSvc, egressDef, ingressDef)
	if err != nil {
		util.Warn("Problem discovering AWS services:", err)
		return
	}

	fmt.Println("==================================================")
	fmt.Println("Discovered Egress Ports:")
	for _, taskPort := range egress {
		displayTaskPort(taskPort)
	}

	fmt.Println("==================================================")
	fmt.Println("Discovered Ingress Ports:")
	for _, taskPort := range ingress {
		displayTaskPort(taskPort)
	}

}


func displayTaskPort(tp *aws.AwsTaskPortInfo) {
	if tp == nil {
		fmt.Println("  - <nil point info>")
		return
	}
	fmt.Println("  - Setup:")
	displayPtrS("                   Service Name: %s", tp.ServiceName)
	displayPtrS("                     Proxy Path: %s", tp.ProxyPath)
	displayPtrS("                         Ref Id: %s", tp.RefId)
	displayPtrS("                    Service ARN: %s", tp.ServiceArn)
	displayPtrS("                   Cluster Name: %s", tp.ClusterName)
	displayPtrS("                    Cluster ARN: %s", tp.ClusterArn)
	fmt.Println("    Task:")
	displayPtrS("                 Container Name: %s", tp.ContainerName)
	displayPtrS("                       Task ARN: %s", tp.TaskArn)
	displayPtrS("                  Container ARN: %s", tp.ContainerArn)
	displayPtrS("            Docker Container ID: %s", tp.DockerRuntimeId)
	displayPtrS("         Container Instance ARN: %s", tp.ContainerInstanceArn)
	displayPtrS("                    Launch Type: %s", tp.LaunchType)
	displayPtrS("            Task Definition ARN: %s", tp.TaskDefinitionArn)
	displayPtrS("  Task Definition Deployment Id: %s", tp.TaskDefinitionDeploymentId)
	displayPtrS("              Container Bind IP: %s", tp.ContainerBindIp)
	displayPtrI("                 Container Port: %d", tp.ContainerPort)
	displayPtrI("                      Host Port: %d", tp.HostPort)
	displayPtrS("                       Protocol: %s", tp.Protocol)
    fmt.Println("    EC2 Instance:")
	displayPtrS("                    Instance Id: %s", tp.ServiceName)
	displayPtrS("                     Public DNS: %s", tp.Ec2InstancePublicDns)
	displayPtrS("                      Public IP: %s", tp.Ec2InstancePublicIp)
	displayPtrS("                    Private DNS: %s", tp.Ec2InstancePrivateDns)
	displayPtrS("                     Private IP: %s", tp.Ec2InstancePrivateIp)
	displayPtrS("                      Subnet Id: %s", tp.Ec2InstanceSubnetId)
}


func displayPtrS(format string, v *string) {
	fmt.Printf(format + "\n", util.AsStr(v))
}

func displayPtrI(format string, v uint32) {
	fmt.Printf(format + "\n", v)
}
