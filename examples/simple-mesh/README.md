# Simple Mesh Example

In this example, we construct a simple mesh based on a simple service ([service-key-forward](service-key-forward)).  We'll be running nightjar through docker-compose entirely from your local computer.

The service itself is configured through environment variables:

* `KEYS` - Comma-separated list of "keys".  Each key is assigned a path, in the form `/key/${key}`, and it returns the JSON data `{"key":"${key}"}`.
* `FORWARD_KEYS` - Comma-separated list of environment variable `keys`, which make up a path and URL to forward to.  Requests to `/forward/${key}` cause the service to make a request to the URL defined in the environment variable `${key}_URL`.  Its response and status code are returned to the caller.
* `${key}_URL` - Path part of the `FORWARDED_KEYS` key element, where `${key}` is the upper-case version of the key.

This simple setup allows us to create complex meshes.
 
## No Mesh

In this case we will simply use two services with no mesh:

* Forwarder F1
    * Service: f1
    * Color: blue
    * Path: `/forward/f1` forwards to `/key/s1`
    * Path: `/key/f1`
* Service S1
    * Service: s1
    * Color: blue
    * Path: `/key/s1`

This very simple setup is detailed in [docker-compose-00.yaml](docker-compose-00.yaml).

Once you start up the configuration:

```bash
docker-compose -f docker-compose-00.yaml up
```

This compose file simply has the f1 service connect directly to the s1 service.  Likewise, there's no gateway into the mesh, so you must contact each one directly.  You can then run REST API requests against each one of those instances. 

```bash
$ curl http://localhost:3001/forward/f1
{"key":"s1"}
$ curl http://localhost:3002/key/s1
{"key":"s1"}
$ curl http://localhost:3001/key/f1
{"key":"f1"}
```

## Introduce Nightjar

For the next example, we'll need the stand-alone version of nightjar's docker image built locally.

```bash
$ cd ../../src
$ docker build -t local/nightjar-standalone -f Dockerfile.envoy-standalone .
```

Then we start [docker-compose-01.yaml](docker-compose-01.yaml) to introduce nightjar as a gateway.  In this case, because the mesh is so simple, the gateway is being shared between all the services as also the sidecar.
