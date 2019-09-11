package aws


func DiscoverServiceDetails(svc *AwsSvc, serviceArns []*string, cluster *string) ([]*AwsTaskPortInfo, error) {
    serviceBuilders, sbErr := LoadServicesForCluster(svc.ecs, serviceArns, cluster)
    if sbErr != nil {
        return []*AwsTaskPortInfo{}, sbErr
    }
    if len(serviceBuilders) <= 0 {
        // Early exit for nothing found.
        return []*AwsTaskPortInfo{}, nil
    }

    return LoadTasks(svc.ecs, serviceBuilders, cluster)
}
