# About

Nightjar containers that are independent of each other.

In this setup, each nightjar container runs a background loop to poll for changes in the AWS Cloud Map configuration, and update the Envoy configuration.

This allows running both private service mesh access and public service mesh access together in a single container.  It also allows for independence and high availability.

## Building

To build this docker image, you need to create the base image.

```bash
( cd ../nightjar-base && docker build -t local/nightjar-base-envoy -f Dockerfile.envoy . )
```

The tag `local/nightjar-base-envoy` is required in order to build the nightjar-standalone image.

Then create the nightjar-standalone image:

```bash
( cd envoy-docker && docker build -t my/nightjar-standalone . )
```

To run the automated tests, run:

```bash
docker build -t my/nightjar-standalone-tests -f Dockerfile.shell-test . && docker run --rm -it my/nightjar-standalone-tests
```

## API Usage

Let's say you have 20 different services in your service mesh.  For high availability purposes, each kind of service has 3 instances running (60 services).  If you want to have blue/green deployment for all of these active at the same time, that brings us to 120 services.

This is now a grand total of 1 Cloud Map namespace, 40 Cloud Map services, and 120 Cloud Map service instances.  There's an extra 1 service instance per service/color, so 160 service instances.

If one nightjar loops over this, it performs 1 service/color lookup to fetch the namespace ID, then 1 lookup per 100 service instances to find all the service/colors in the namespace (for 40 service/colors, that's 1 calls).  Then, for *each service/color*, there is 1 lookup per 100 service instances in that service/color to find all the instances (3 instances + 1 service metadata per service, for 39 services, is 39 calls; nightjar does not route to itself).  So far, this gives us 41 calls.  And this is for just one check.

If nightjar checks twice a minute, that means it checks 2,880 times a day.  That's 118,080 calls per day.  Right now, the fee is $1.00 per 1 million requests, or $0.11 per day, or $43.09 per year.

For some people, this is the price of their web hosting; for others, it's chump change in comparison to the rest of their AWS bill.  It's your call.


## `shared-volume-docker`

***EXPERIMENTAL***

This is an alternate approach to the deployment that uses the envoy docker image as-is, ands puts the Nightjar standalone inspection source into another container.

With this approach, the envoy container must be defined with shared volume, and passes in the bootstrap configuration through the task arguments.  If you desire the bootstrap configuration to change, then alter the container's definition and create the new container.  The bootstrap configuration will define the dynamic parameters as located in the shared volume that the Nightjar standalone inspection container writes into.  

The Envoy container should have this command value:

```bash
"--config"
"{node:{id:${SERVICE_MEMBER},cluster:${SERVICE_CONTAINER_NAME}},admin:{access_log_path:/dev/stdout,address:{socket_address:{address:0.0.0.0,port_value:${ENVOY_ADMIN_PORT}}}},dynamic_resources:{cds_config:{path:/mnt/envoy-config/active-envoy-config/cds.yaml},lds_config:{path:/mnt/envoy-config/active-envoy-config/lds.yaml}}"
```

The method used for launching this image should correctly replace the variables above: `ENVOY_ADMIN_PORT`, `SERVICE_PORT`, `SERVICE_MEMBER` and `ENV SERVICE_CONTAINER_NAME`.
