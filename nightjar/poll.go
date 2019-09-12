package nightjar

import (
    "fmt"
    "time"

    "github.com/groboclown/nightjar-mesh/nightjar/enviro"
    "github.com/groboclown/nightjar-mesh/nightjar/aws"
    "github.com/groboclown/nightjar-mesh/nightjar/envoy"
    "github.com/groboclown/nightjar-mesh/nightjar/util"
)


func Poll() {
    awsSvc := aws.NewAwsSvc(true)
    waitTime := enviro.ReadWaitTime()
    egressDef := enviro.ReadEgress()
    ingressDef := enviro.ReadIngress()
    envoySvc := envoy.NewEnvoySvc(enviro.ReadEnvoy(), func (err error) {
        fmt.Println("[ERROR] Envoy problem:", err)
    })

    oldEgress := make([]*aws.AwsTaskPortInfo, 0)
    oldIngress := make([]*aws.AwsTaskPortInfo, 0)

    for {
        util.Debug("Loading AWS services...")
        egress, ingress, aErr := aws.DiscoverInOutTasks(awsSvc, egressDef, ingressDef)
        if aErr != nil {
            util.Warn("Problem discovering AWS services:", aErr)
        } else {
            if err := envoy.UpdateEgress(aws.FindDiffs(oldEgress, egress), envoySvc); err != nil {
                util.Warn("Problem updating the Envoy proxy for egress settings:", err)
            } else {
                oldEgress = egress
            }
            if err := envoy.UpdateIngress(aws.FindDiffs(oldIngress, ingress), envoySvc) ; err != nil {
                util.Warn("Problem updating the Envoy proxy for ingress settings:", err)
            } else {
                oldIngress = ingress
            }            
        }

        time.Sleep(waitTime * time.Millisecond)
    }
}
