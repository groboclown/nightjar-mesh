package discovery


// OLD CRUFT


import (
    //"github.com/aws/aws-sdk-go/aws"
    //"github.com/aws/aws-sdk-go/aws/awserr"
    "github.com/aws/aws-sdk-go/service/ecs"
    "github.com/aws/aws-sdk-go/service/elbv2"
)


/**
 * Loads the Application Load Balancer information for all services.
 *
 * Updates the builders with:
 *
 *   targetGroups[]:
 *      loadBalancerArn, balancerDns, hostedZoneId, vpcId, listenerArn,
 */
func load_elb(elbSvc *elbv2.ELBV2, builders []service_builder) error {
    // Gather up all the load balancers.
    balancers := make([]*string, len(builders))
    balancerTargets := make(map[string][]target_group)
    for builder := range builders {
        for tg := range builder.target_group {
            groups, ok := balancerTargets[tg.loadBalancerArn]
            if ! ok {
                groups = make([]target_group, 1)
                balancers = append(balancers, &tg.loadBalancerArn)
            }
            groups = append(groups, tg)
            balancerTargets[tg.loadBalancerArn] = groups
        }
    }

    lbErr := loop_over_load_balancers(
        elbSvc, balancers,
        func (lb *elbv2.LoadBalancer) {
            if groups, ok := balancerTargets[lb.loadBalancerArn] ; ok {
                for tg := range groups {
                    tg.loadBalancerArn = lb.LoadBalancerArn
                    tg.balancerDns = lb.DNSName
                    tg.hostedZoneId = lb.CanonicalHostedZoneId
                    tg.vpcId = lb.VpcId
                }
            }
        },
    )
    if lbErr != nil {
        return lbErr
    }

    // This requires an extra call for every load balancer, but has no gain.
    // for balancerArn, groups := balancerTargets {
    //     lnErr := elbSvc.DescribeListenersPages(
    //         &DescribeListenersInput{ LoadBalancerArn: &balancerArn },
    //         func (output *DescribeListenersOutput, lastPage bool) bool {
    //             for listener := output.Listeners {
    //                 for group := range groups {
    //                     if *(group.balancerPort) == *(listener.Port) {
    //                         group.listenerArn = listener.ListenerArn
    //                     }
    //                 }
    //             }
    //             return true
    //         }
    //     )
    //     if lnErr != nil {
    //         return lnErr
    //     }
    // }

    return nil
}


func loop_over_load_balancers(elbSvc *elbv2.ELBV2, balancerArns []*string, fn func (*LoadBalancer)) error {
    func paged(output *elbv2.DescribeLoadBalancersOutput, lastPage bool) bool {
        if output != nil {
            for lb := range output.LoadBalancers {
                if lb != nil {
                    fn(lb)
                }
            }
        }
        return true
    }

    // Query at most 20 per shot.  It's the API limit.
    for i := 0 ; i < len(balancerArns) ; {
        page := make([]*string, 20)
        for ; len(page) < 20 && i < len(balancerArns) ; i += 1 {
            page = append(page, balancerArns[i])
        }
        lbErr := elbSvc.DescribeLoadBalancersPages(
            &elbv2.DescribeLoadBalancersInput{
                LoadBalancerArns: page,
            },
            paged,
        )
        if lbErr != nil {
            return lbErr
        }
    }
    return nil
}
