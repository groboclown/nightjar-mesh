# nightjar-mesh

An AWS ECS Control Plane with Envoy Proxy

*That's a fancy way to say that Nightjar monitors AWS Elastic Cloud Services for changes, and sends updates to a local Envoy Proxy to update the traffic routes.*


## About

[Nightjar](https://en.wikipedia.org/wiki/Nightjar) is a **Control Plane** for [Envoy Proxy](https://envoyproxy.github.io/envoy/), designed to run within the Amazon Web Services (AWS) ecosystem.  It uses [AWS Cloud Map](https://aws.amazon.com/cloud-map/) to configure how the Envoy **data plane** operates within the Elastic Cloud Services (ECS).

![2 services communicating through nightjar + Envoy Proxy](2-service-traffic.svg)

Nightjar loads the service configuration defined in AWS Cloud Map and updates the Envoy Proxy configuration.  It then periodically scans AWS for updates and changes Envoy as the network changes.  Nightjar works both for network traffic entering the data plane and for traffic within the plane.

![Traffic flow within a service mesh, deploying a blue-green mix of service #2](nightjar-service-mesh.svg)

AWS provides their [App Mesh](https://aws.amazon.com/app-mesh/) tooling, but it involves many limitations that some deployments cannot work around, or should not work around.  Nightjar acts as a low-level intermediary between the AWS API and the Envoy Proxy to make deployments in EC2 or Fargate possible, with little fuss.  It even works without `awsvpc` networks, and takes advantage of ephemeral ports.


## Some Notes on Terminology

For the purposes of this document, the phrase **service mesh** refers to the set of services that communicate with each other through private channels.  Normally this is called a "cluster", but that word is avoided here because of the many different AWS services that have their own meaning of the word (i.e. an ECS cluster, which is very different).  It's possible to run multiple service meshes that communicate with each other, but these should communicate only through public routes. 
 
Envoy manages the **data plane**, which refers to the control of the flow of network traffic between the services within the service mesh.  The Envoy Proxy documentation describes all the goodness that the tool provides.  Nightjar gives you the flexibility to adjust the Envoy configuration to suit exactly your needs.

The **control plane** manages the configuration of the data plane.  Normal documentation on control planes with Envoy Proxy refer to a dynamic configuration of Envoy with another service managing it.  Instead, Nightjar generates configuration files which Envoy loads when they are refreshed.  This means the Nightjar tooling just needs to be in-memory when necessary, and not consume another container.

**Nightjar** refers to the control plane tool, while **nightjar-mesh** refers to the Nightjar docker sidecar, the network topology, and the AWS resources used in the construction of the mesh.


## How It Works

You add the Nightjar container to an [ECS Task Definition](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definitions.html), along with your existing service container.  The Nightjar container runs the Envoy proxy, and is considered a "sidecar" container here.  The service must be configured to send all traffic to other services in the service mesh to the Nightjar container.  Inbound traffic to the service comes from the Nightjar containers running in the other services. 

You configure the Nightjar container with two sets of properties:

* The local [service name](https://docs.aws.amazon.com/cloud-map/latest/dg/working-with-services.html).  This tells Nightjar to not handle traffic sent to this local container.  It also indirectly tells Nightjar which service mesh it belongs to.
* The other [service mesh names](https://docs.aws.amazon.com/cloud-map/latest/dg/working-with-namespaces.html).  If you split your network into multiple service meshes, then each of the other meshes is defined by name and can direct traffic directly within the other mesh.  This is completely optional; you can instead direct all other service mesh traffic to not go through the local Envoy Proxy.

To setup the services, you need to register your tasks using AWS Cloud Map (aka Service Discovery) using SVR registration.  This makes available to Nightjar the service members and how to connect to them.

Note that there are many more configuration possibilities with Nightjar.  It's constructed to give you the power to setup Envoy how you want it.


## Using Nightjar

Using Nightjar involves registering your services with AWS Cloud Map, adding a specially named service registration instance to cloud map that describes metadata for your service, and adding the Nightjar sidecar container to your services.

The primary power from Nightjar is the [Cloud Map data extraction tool](nightjar-src/generate_template_input_data.py), which uses your AWS Cloud Map configuration, plus a few environment variables to tell it where to look.  Everything else is window dressing to make it easy to use.

### Cloud Map Data Processing

It uses these environment variables to configure its operation:

* `SERVICE_MEMBER` (required, no default).  The AWS Cloud Map service ID (not the ARN) of the service to which this Nightjar sidecar belongs to.  It will be in the form `svg-randomlettersandnumbers`; see the example below for how to set this value easily from a CFT.  Set this to `-gateway-` to have Nightjar run in "gateway" mode, where it does not run as a sidecar to another service container, but instead as a gateway proxy into the service mesh.
* `SERVICE_PORT` (defaults to 8080).  The port number that the envoy proxy will listen for requests that are sent to other services within the `SERVICE_MEMBER` namespace.
* `NAMESPACE_x` where *x* is some number between 0 and 99.  This defines a AWS Cloud Map service namespace other than the `SERVICE_MEMBER` namespace, which Nightjar will forward requests.
* `NAMESPACE_x_PORT`.  The listening port number that the Envoy proxy will forward requests into the corresponding `NAMESPACE_x` service namespace.  Services send a request to the Nightjar container on this port number to connect to the other namespace.
* `AWS_REGION` (required, no default). The AWS region name (i.e. `us-west-2`) in which the Cloud Map registration is managed.
* `ENVOY_ADMIN_PORT` (defaults to 9901). the Envoy proxy administration port.

The `SERVICE_MEMBER` must reference a [Cloud Map service](https://docs.aws.amazon.com/cloud-map/latest/dg/working-with-services.html) with SVC DNS registration, which has all the ECS services for that service registered as [instances](https://docs.aws.amazon.com/cloud-map/latest/dg/working-with-instances.html).  In addition, it must also have a special service instance with ID `service-settings` and the given keys:

* `SERVICE` - the name of the service.
* `COLOR` - the deployment "color" (usually blue or green).
* `AWS_INSTANCE_IPV4` and `AWS_INSTANCE_PORT` - these keys are required by AWS, but the value doesn't matter for the purposes of Nightjar.
* For each path prefix that the service handles, register that path as the key, and the relative weight that this service instance should be assigned to that prefix.  For example, if the "blue" deployment has just been released and you want to lightly load it before switching over, give its paths a number significantly lower than the "green" deployment.  If the path is explicitly only used within the service mesh, and should never be accessible from outside this mesh, then prepend a question mark ('?') to the start of the key.  Note that to be recognized as a path key, the key must start with a `/`, `?`, or `*`.

### Envoy Proxy Configuration

The Cloud Map extracted data conforms to the [data format](nightjar-src/generation-data-schema.yaml), and is used as input to [mustache templates](https://en.wikipedia.org/wiki/Mustache_%28template_system%29), to construct the Envoy Proxy configuration.

By default, Nightjar provides [configuration templates](nightjar-src/templates) that generate a simple Envoy Proxy configuration.  However, you can change these files to suit your needs.

* In a child Docker image, you can add a new template directory.  Add in all the files you want to here.  Any file that ends in `.mustache` will be converted using the Cloud Map extracted data; everything else is used as-is.  Note that sub-directories are currently not supported for mustache template support.
* Set the environment variable `ENVOY_TEMPLATE_DIR` to point to the new template directory.
* The default boot configuration file used to start up Envoy is named `envoy-config.yaml`.  If you want to change this to a different file name, set the `ENVOY_CONFIGURATION_FILE` to the file name (without the directory).

### Runtime Execution

Additionally, you can tweak the operation of Nightjar with these options:

* Environment variable `REFRESH_TIME`: (defaults to 30) the number of seconds between polling for updates in the configuration. 
* Environment variable `EXIT_ON_GENERATION_FAILURE`: (defaults to 0)  If this value is *anything* other than `0`, then the container will stop if an error occurs while generating the envoy proxy static configuration file.
* Environment variable `FAILURE_SLEEP`: (defaults to 300) if the generation failed, the process will wait this many seconds before stopping the container.  This allows an operator time to inspect the container for problems.
* Environment variable `ENVOY_LOG_LEVEL`: (no default) Sets the Envoy proxy logging level.
* Environment variable `DEBUG_CONTAINER`: (no default) set this to `1` to start the container as a shell, to help in debugging the container.

There are several others, if you're really interested.  See the [script](nightjar-src/run-loop.sh) for details.


## Words of Warning

For large clusters, you may find yourself running into the AWS `ServiceDiscovery::ListNamespaces` throttling limit.  If this happens, you may want to make the `REFRESH_TIME` environment variable larger. 

## Example of Nightjar with a Service

Control planes are not easy insert into your network topology.  However, Nightjar attempts to make the configuration as minimal as possible to make the configuration simple and easy to debug.

### AWS Account

First, you need an AWS account with access to a VPC, at least 2 subnets in different activity zones, ECS, an ECS cluster, the ability to create IAM roles, and Cloud Map.  The setup here uses CloudFormation templates to build up the example, but you don't need to use that.  It's just incredibly helpful in keeping the system together.

### CloudFormation Template Setup

The CloudFormation template ("CFT") starts off with some parameters to get us going.  For this example, we will deploy the containers in EC2 instances.  A few tweaks can make this work in Fargate.

```yaml
Parameters:
  ClusterName:
    Type: String
    Description: >
      The ECS cluster name or ARN in which the image registry task will run.

  VPC:
    Type: AWS::EC2::VPC::Id
    Description: >
      The VPC to connect everything to.

  Subnets:
    Type: List<AWS::EC2::Subnet::Id>
    Description: >
      The subnets in the VPC for the service to run in.
      Be careful of cross-AZ data charges!

  ECSInstancesSecurityGroup:
    Type: String
    Description: >
      Security group for the EC2 cluster instances.  This is a "shared key" that
      must be given to anything that wants to talk to the EC2 cluster.
```

### Add In Our Service

Let's add in a single service to the stack, called `tuna`.  Note that having a single service means that we don't need a whole service mesh, but this shows all the resources necessary before we add in the "meshiness".  And it keeps our example simple.

Note that this prepares us for blue/green deployments, by labeling this service's resources with "blue".  To add in a canary test of a service, a copy of the "blue" resources is made with a different color name for only that one service.

```yaml
Resources:
  TunaBlueService:
    Type: "AWS::ECS::Service"
    Properties:
      Cluster: !Ref "ClusterName"
      DeploymentConfiguration:
        MaximumPercent: 200
        MinimumHealthyPercent: 100
      DesiredCount: 1
      LaunchType: EC2
      TaskDefinition: !Ref "TunaBlueTaskDef"

  TunaBlueTaskDef:
    Type: "AWS::ECS::TaskDefinition"
    Properties:
      RequiresCompatibilities:
        - EC2
      # No network definition, which means to use the EC2 standard bridge networking mode.
      ExecutionRoleArn: !Ref TaskExecRole
      TaskRoleArn: !Ref ServiceTaskRole
      Family: "yummy-tuna-blue"
      Tags:
        # Generally good practice to help you out in a production environment.
        - Key: color
          Value: blue
        - Key: service
          Value: tuna
      ContainerDefinitions:
        - Name: service
          Image: !Sub "${AWS::AccountId}.dkr.ecr.${AWS::Region}.amazonaws.com/tuna:latest"
          Essential: true
          Cpu: 256
          MemoryReservation: 1024
          PortMappings:
            - ContainerPort: 3000
              # No "HostPort", which makes this an ephemeral port.
              Protocol: "tcp"

  TaskExecRole:
    DependsOn:
    - ServiceTaskRole
    Type: AWS::IAM::Role
    Properties:
      Path: "/"
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: Allow
            Principal:
              Service:
                - "ecs-tasks.amazonaws.com"
            Action:
              - "sts:AssumeRole"
      Policies:
        - PolicyName: LaunchContainer
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Effect: Allow
                Action:
                  - "ecr:GetAuthorizationToken"
                  - "ecr:BatchCheckLayerAvailability"
                  - "ecr:GetDownloadUrlForLayer"
                  - "ecr:BatchGetImage"
                  - "logs:CreateLogStream"
                  - "logs:PutLogEvents"
                Resource:
                  - "*"
              -Effect: Allow
                Action:
                  - "iam:PassRole"
                Resource:
                  - !GetAtt "ServiceTaskRole.Arn"
              - Effect: Allow
                Action:
                  - "ecs:RunTask"
                  - "ecs:StartTask"
                  - "ecs:StopTask"
                Resource:
                  - "*"

  ServiceTaskRole:
    Type: AWS::IAM::Role
    Properties:
      Path: "/"
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: Allow
            Principal:
              Service:
                - "ecs-tasks.amazonaws.com"
            Action:
              - "sts:AssumeRole"
      # Add policies as necessary.
      # This definition here allows for logging
      # and writing to an XRay daemon.
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/CloudWatchFullAccess
        - arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess

      # These policies are for the Nightjar container, which will be
      # added later.  For a real production environment, you will want to
      # separate out the permissions into minimal chunks that allow the
      # container to work.  But, all containers within an ECS service must
      # share the same IAM role.
      Policies:
      - PolicyName: ServicePlusNightjar
        PolicyDocument:
          Version: "2012-10-17"
          Statement:
            - Effect: Allow
              Action:
                - "servicediscovery:List*"
                - "servicediscovery:Get*"
              Resource:
                - "*"
```

This creates the service, which starts the container in our ECS cluster.  The only way to connect to this service is through the ephemeral port on the EC2 instance, which is above the 32768 range.

On a side note, using ephemeral ports means that you must have a large number of ports open in a security group to allow access to any of the containers.  The alternative approach is to explicitly restrict container ports to a specific host port, but that makes the configuration less flexible.  Either way you do this, Nightjar will detect the correct port.

### Add in Service Discovery

Nightjar uses AWS Cloud Map for storing the configuration information and location of all the services and their container instances.  Below is the additional and changed resources to the growing CFT.  While we're here, we'll name the network `yummy`, because tuna can be yummy (YMMV). 

```yaml
Resources:
  # The namespace for this mesh.  If we have multiple meshes, each one has its
  # own namespace.  The primary reason to split separate clusters is due to
  # overlapping listening paths for the services.  Another reason is better network
  # traffic control.  It can also add extra security by limiting which paths
  # an outside service can talk to by use of the "private" paths. 
  YummyNamespace:
    Type: "AWS::ServiceDiscovery::PrivateDnsNamespace"
    Properties:
      Description: "The Yummy Mesh"
      Name: "yummy.service.local"
      Vpc: !Ref VPC

  # All the different color deployments of the Tuna have their
  # own discovery record.  
  TunaBlueServiceDiscoveryRecord:
    Type: 'AWS::ServiceDiscovery::Service'
    Properties:
      Name: tuna-blue
      DnsConfig:
        NamespaceId: !Ref "YummyNamespace"
        DnsRecords:
          # Containers add themselves into this record, and with the SRV
          # type, they register the IP and the ephemeral port they listen on. 
          - Type: SRV
            TTL: 300
      HealthCheckCustomConfig:
        FailureThreshold: 1

  # Update the service to include registration 
  TunaBlueService:
    Type: "AWS::ECS::Service"
    Properties:
      Cluster: !Ref "ClusterName"
      DeploymentConfiguration:
        MaximumPercent: 200
        MinimumHealthyPercent: 100
      DesiredCount: 1
      LaunchType: EC2
      TaskDefinition: !Ref "TunaBlueTaskDef"
      ServiceRegistries:
        - RegistryArn: !GetAtt "TunaBlueServiceDiscoveryRecord.Arn"
          # The container name and port of the service we're registering.
          ContainerName: service
          ContainerPort: 3000
```

If the Tuna container goes down, or if it scales up with 16 running containers, then the service discovery instances are also updated to reflect that changing topology.  That's part of the magic of that `ServiceRegistries` key.

That seems like a lot of work to setup just one container, and it is, but that's the boilerplate we need to get started with a mesh.

### Add in Nightjar

With all that boilerplate out of the way, adding in Nightjar to the template is now trivial.  It's just adding in a new container to the existing task definition with some special properties, and adding a link from the service to the Nightjar container, and add in a special meta-data service discovery instance to tell Nightjar about the service it's running in.

```yaml

  # A data-only service discovery instance.  Each discovery service includes
  # one of these to tell Nightjar additional meta-data about the specific
  # service.  This includes the different paths.
  TunaBlueReferenceInstance:
    Type: AWS::ServiceDiscovery::Instance
    Properties:
      # The instance ID MUST be "service-settings"; Nightjar looks for this ID.
      InstanceId: service-settings
      ServiceId: !Ref "TunaBlueServiceDiscoveryRecord"
      InstanceAttributes:
        # High level information about the service/color.
        SERVICE: tuna
        COLOR: blue

        # If your service uses HTTP2, then set this attribute and value.
        HTTP2: enabled
        
        # List of all the URI path prefixes that receive traffic as the
        # keys, and the value is the relative weight to assign this
        # service/color for this path.
        "/tuna": "100"
        
        # Note that the paths weights above can be changed outside this file,
        # through the Cloud Map UI or through the AWS cli.


        # These settings are required for SRV records, but for this
        # meta-data record, the values are never used.  So we set these to
        # valid values that are harmless.
        AWS_INSTANCE_IPV4: 127.0.0.1
        AWS_INSTANCE_PORT: 1234

  TunaBlueTaskDef:
    Type: "AWS::ECS::TaskDefinition"
    Properties:
      RequiresCompatibilities:
        - EC2
      ExecutionRoleArn: !Ref TaskExecRole
      TaskRoleArn: !Ref ServiceTaskRole
      Family: "yummy-tuna-blue"
      Tags:
        - Key: color
          Value: blue
        - Key: service
          Value: tuna
      ContainerDefinitions:
        - Name: service
          Image: !Sub "${AWS:AccountId}.dkr.ecr.${AWS::Region}.amazonaws.com/tuna:latest"
          Essential: true
          Cpu: 256
          MemoryReservation: 1024
          PortMappings:
            - ContainerPort: 3000
              Protocol: "tcp"
          
          # New!  Allow the service to use nightjar as an egress proxy.
          Link:
            - nightjar

        # New container!
        - Name: nightjar
          # Note: this is not a real image name.  You need to build it yourself.
          Image: locally/built/nightjar
          User: "1337"
          Essential: true
          Memory: 128
          Ulimits:
            - Name: nofile
              HardLimit: 15000
              SoftLimit: 15000
          Environment:
            # These environment variables must be carefully set.
  
            # The AWS region, so Nightjar can ask for the right resources.
            - Name: AWS_REGION
              Value: !Ref "AWS::Region"

            # Which service record that defines the service in which Nightjar runs.
            - Name: SERVICE_MEMBER
              Value: !Ref "TunaBlueServiceDiscoveryRecord"
  
            # The port number that the envoy proxy will listen to for connections
            # *from* the sidecar service *to* the service mesh.
            - Name: SERVICE_PORT
              Value: 8090
          PortMappings:
            # The SERVICE_PORT above
            - ContainerPort: 8090
              Protocol: tcp

            # You can optionally also make the Envoy admin port
            # available.  This defaults to 9901, but can be set with
            # the ENVOY_ADMIN_PORT environment variable.
            # - ContainerPort: 9901
            #   Protocol: tcp    
          HealthCheck:
            Command:
              - "CMD-SHELL"
              - "curl -s http://localhost:9901/server_info | grep state | grep -q LIVE"
            Interval: 5
            Timeout: 2
            Retries: 3

```

In this example, the Nightjar Envoy Proxy will listen to port 8090 for connections from the Tuna service to the the rest of the service mesh.  Because the Nightjar container is named `nightjar`, and the Tuna service includes a link to `nightjar`, the Tuna service should call to `http://nightjar:8090` plus the other service's path to connect to it.  For example, if the normal call to a dependent service is `http://marlin:3000/nicknames`, then the tuna service would call out to `http://nightjar:8090/nicknames`.


### Adding Another Service

If we want to add another service to the mesh, it's mostly cut-n-paste of the above.  The one thing to note is that *the tuna service setup does not change.*  Nightjar picks up the new service from the namespace and adds in the weighted paths.  This can be done even without stopping the Tuna service.


### Adding a Service Mesh Gateway

You could use a standard Application Load Balancer for every service, but that means you don't gain the great network shaping that Envoy gives us.  Instead, we want to take advantage of the envoy goodness, but that means introducing a gateway service that all outside traffic uses to access the service mesh, and that includes a load balancer.

Nightjar produces this with just a few tweaks.  You'll want to set the nightjar container as the only container in the gateway, and configure it as a gateway.

```yaml
  # Setup the gateway service + container definition.
  GatewayService:
    Type: AWS::ECS::Service
    DependsOn:
      - GatewayTargetGroup
      - GatewayLoadBalancerListener
    Properties:
      Cluster: !Ref "ClusterName"
      DeploymentConfiguration:
        MaximumPercent: 200
        MinimumHealthyPercent: 100
      DesiredCount: 1
      LaunchType: EC2
      # The gateway is accessible through a load balancer.
      LoadBalancers:
        - ContainerName: nightjar
          ContainerPort: 2000
          TargetGroupArn: !Ref GatewayTargetGroup
      TaskDefinition: !Ref GatewayTaskDef
  
  GatewayTaskDef:
    Type: "AWS::ECS::TaskDefinition"
    DependsOn:
      - YummyNamespace
    Properties:
      RequiresCompatibilities:
        - EC2
      ExecutionRoleArn: !Ref TaskExecRole
      TaskRoleArn: !Ref ServiceTaskRole
      Family: "yummy-gateway"
      Tags:
        - Key: color
          Value: gateway
        - Key: service
          Value: gateway
      ContainerDefinitions:
        - Name: nightjar
          Image: locally/built/nightjar
          User: "1337"
          Essential: true
          Memory: 128
          Ulimits:
            - Name: nofile
              HardLimit: 15000
              SoftLimit: 15000
          Environment:
            # To configure Nightjar as a gateway, we assign it a special reserved name.
            - Name: SERVICE_MEMBER
              Value: "-gateway-"
            # It will not think of itself as part of a service, so it won't ignore any
            # paths.  Instead, it listens for connections on the mesh, defined using
            # the namespace information.
            - Name: NAMESPACE_1
              Value: !Ref YummyNamespace
            # This is the port that the load balancer is forwarding to on this container.
            - Name: NAMESPACE_1_PORT
              Value: "2000"
  
            # All these are the same maning from what we saw before...
            - Name: AWS_REGION
              Value: !Ref "AWS::Region"
            - Name: ENVOY_ADMIN_PORT
              Value: 9901
          PortMappings:
            - ContainerPort: 9901
              Protocol: tcp
            # The NAMESPACE_1_PORT
            - ContainerPort: 2000
              Protocol: tcp
          HealthCheck:
            Command:
              - "CMD-SHELL"
              - "curl -s http://localhost:9901/server_info | grep state | grep -q LIVE"
            Interval: 5
            Timeout: 2
            Retries: 3

  GatewayTargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Name: gateway-tg
      # The listening port of the container, which nightjar will forward to the mesh
      Port: 2000
      Protocol: HTTP
      VpcId: !Ref VPC
      TargetGroupAttributes:
        - Key: deregistration_delay.timeout_seconds
          Value: 120
      HealthCheckIntervalSeconds: 60
      # Hard-coded health check path on the envoy proxy.
      HealthCheckPath: '/ping'
      Matcher:
        HttpCode: "200"
      HealthCheckProtocol: HTTP
      HealthCheckTimeoutSeconds: 5
      HealthyThresholdCount: 2
      UnhealthyThresholdCount: 2

  GatewayLoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Scheme: internal
      LoadBalancerAttributes:
        - Key: idle_timeout.timeout_seconds
          Value: '300'
      Subnets: !Ref Subnets
      SecurityGroups:
        - !Ref LoadBalancerSecurityGroup
        - !Ref ECSInstancesSecurityGroup
  GatewayLoadBalancerListener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    DependsOn:
      - GatewayLoadBalancer
    Properties:
      DefaultActions:
        - TargetGroupArn: !Ref GatewayTargetGroup
          Type: 'forward'
      LoadBalancerArn: !Ref 'GatewayLoadBalancer'
      # The load balancer listening port.
      Port: 80
      Protocol: HTTP

  LoadBalancerSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Access to the fronting load balancer
      VpcId: !Ref VPC
      SecurityGroupIngress:
          # You should probably change this to something safer.
          - CidrIp: 0.0.0.0/0
            IpProtocol: -1

```

If you have paths you want Nightjar to not make available in the gateways (they are "private" within the service mesh), then, in the `service-settings` service registration instance, prefix the path with a question mark:

```yaml
  TunaBlueReferenceInstance:
    Type: AWS::ServiceDiscovery::Instance
    Properties:
      InstanceId: service-settings
      ServiceId: !Ref "TunaBlueServiceDiscoveryRecord"
      InstanceAttributes:
        AWS_INSTANCE_IPV4: 127.0.0.1
        AWS_INSTANCE_PORT: 1234
        SERVICE: tuna
        COLOR: blue
        # public path; the gateway forwards these.
        "/tuna": "65"
        
        # private path; the gateway does not forward these.
        "?/albacore": "100"
```

A question mark was chosen because that character has special meaning for URIs - it can't be part of a path (it's the query separator).  Nightjar will remove the leading question mark when constructing the Envoy route configuration.
