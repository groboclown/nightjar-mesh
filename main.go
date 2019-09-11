package main

import (
    "fmt"
    "time"

    "github.com/groboclown/nightjar-mesh/nightjar/enviro"
    "github.com/groboclown/nightjar-mesh/nightjar/aws"
    "github.com/groboclown/nightjar-mesh/nightjar/envoy"
)

func main() {
    awsSvc := aws.NewAwsSvc()
    waitTime := enviro.ReadWaitTime()
    services := enviro.ReadEgress()
    tasks := enviro.ReadIngress()
    envoySvc := envoy.NewEnvoySvc(enviro.ReadEnvoy(), func (err error) {
        fmt.Println("[ERROR] Envoy problem:", err)
    })

    oldEgress := make([]*aws.AwsTaskPortInfo, 0)
    oldIngress := make([]*aws.AwsTaskPortInfo, 0)

    for {
        // fmt.Println("[DEBUG] loading services...")
        egress, ingress, err := aws.DiscoverInOutTasks(awsSvc, services, tasks)
        if err != nil {
            fmt.Println("[ERROR] Problem discovering AWS services:", err)
        } else {
            envoy.UpdateEgress(aws.FindDiffs(oldEgress, egress), envoySvc)
            envoy.UpdateIngress(aws.FindDiffs(oldIngress, ingress), envoySvc)
            oldEgress = egress
            oldIngress = ingress
        }

        time.Sleep(waitTime * time.Millisecond)
    }
}
