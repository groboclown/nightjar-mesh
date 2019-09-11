package aws

import (
    //"github.com/aws/aws-sdk-go/aws"
    //"github.com/aws/aws-sdk-go/aws/awserr"
    "github.com/aws/aws-sdk-go/aws/session"
    //"github.com/aws/aws-sdk-go/service/ec2"
    "github.com/aws/aws-sdk-go/service/ecs"
    //"github.com/aws/aws-sdk-go/service/elbv2"
)


type AwsSvc struct {
    ecs		*ecs.ECS
}


func NewAwsSvc() *AwsSvc {
    sess := session.Must(session.NewSession())
    ecsSvc := ecs.New(sess)
    // anything else we may want...
    return &AwsSvc{ecs: ecsSvc}
}
