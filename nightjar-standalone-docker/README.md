# About

Nightjar containers that are independent of each other.  In this setup, each nightjar container runs a background loop to poll for changes in the AWS Cloud Map configuration, and update the Envoy configuration.

This allows running both private service mesh access and public service mesh access together in a single container.

## API Usage

Let's say you have 20 different services in your service mesh.  For high availability purposes, each kind of service has 3 instances running (60 services).  If you want to have blue/green deployment for all of these active at the same time, that brings us to 120 services.

This is now a grand total of 1 Cloud Map namespace, 40 Cloud Map services, and 120 Cloud Map service instances.  There's an extra 1 service instance per service/color, so 160 service instances.

If one nightjar loops over this, it performs 1 service/color lookup to fetch the namespace ID, then 1 lookup per 100 service instances to find all the service/colors in the namespace (for 40 service/colors, that's 1 calls).  Then, for *each service/color*, there is 1 lookup per 100 service instances in that service/color to find all the instances (3 instances + 1 service metadata per service, for 39 services, is 39 calls; nightjar does not route to itself).  So far, this gives us 41 calls.  And this is for just one check.

If nightjar checks twice a minute, that means it checks 2,880 times a day.  That's 118,080 calls per day.  Right now, the fee is $1.00 per 1 million requests, or $0.11 per day, or $43.09 per year.
