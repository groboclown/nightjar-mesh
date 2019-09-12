package envoy

import (
    "github.com/groboclown/nightjar-mesh/nightjar/aws"
)


func UpdateEgress(diffs *aws.AwsTaskPortInfoDiffs, envoySvc *EnvoySvc) error {
    if diffs == nil || envoySvc == nil || (len(diffs.Removed) <= 0 && len(diffs.Added) <= 0) {
        // Nothing to do
        return nil
    }

    return nil
}
