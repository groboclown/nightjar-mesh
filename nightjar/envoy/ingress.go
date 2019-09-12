package envoy

import (
    "github.com/groboclown/nightjar-mesh/nightjar/aws"
)


/**
 * Update the external connections incoming to the local ECS service
 * (ingress proxy).  This will update the clusters and the existing
 * endpoints.
 *
 * Because the queries for the services fetches everything, 
 */
func UpdateIngress(diffs *aws.AwsTaskPortInfoDiffs, envoySvc *EnvoySvc) error {
    if diffs == nil || envoySvc == nil || (len(diffs.Removed) <= 0 && len(diffs.Added) <= 0) {
        // Nothing to do
        return nil
    }

    return nil
}
