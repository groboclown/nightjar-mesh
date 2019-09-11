package envoy

import (
    "github.com/groboclown/nightjar-mesh/nightjar/aws"
)


func UpdateIngress(diffs *aws.AwsTaskPortInfoDiffs, envoySvc *EnvoySvc) {
    if diffs == nil || envoySvc == nil || (len(diffs.Removed) <= 0 && len(diffs.Added) <= 0) {
        // Nothing to do
        return
    }
}
