package aws


func FindDiffs(beforeList []*AwsTaskPortInfo, afterList []*AwsTaskPortInfo) *AwsTaskPortInfoDiffs {
    removed := make([]*AwsTaskPortInfo, 0, len(beforeList))
    copy(removed, beforeList)

    added := make([]*AwsTaskPortInfo, len(afterList))
    for _, after := range afterList {
        matched := false
        for _, before := range beforeList {
            // Find the index of the before item in the removed list.
            index := -1
            for idx, v := range removed {
                if before == v {
                    index = idx
                    break
                }
            }
            if index < 0 {
                // This item has already been found; ignore it.
                continue
            }

            // Pointers can be compared, because they all come from the
            // shared value in the PathRef.
            if after.RefId == before.RefId && isEqual(before, after) {
                matched = true
                // Remove from the list
                removed = append(removed[:index], removed[index+1:]...)
                break
            }
        }
        if ! matched {
            added = append(added, after)
        }
    }

    return &AwsTaskPortInfoDiffs{
        Removed: removed,
        Added: added,
    }
}


func isEqual(left *AwsTaskPortInfo, right *AwsTaskPortInfo) bool {
    // Already know that the RefId matches, just need to check everything else that matters
    // in terms of a proxy.

    // By having the RefId match, it means the basic container name, service ARN,
    // cluster name, and container port all match.

    return (
        *left.ContainerInstanceArn == *right.ContainerInstanceArn &&
        *left.HostPort == *right.HostPort &&
        *left.Protocol == *right.Protocol)
}
