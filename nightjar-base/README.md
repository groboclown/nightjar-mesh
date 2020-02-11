# About

The base docker container shared between the different nightjar implementations.  There are many common files that they all use, and this container centralizes them, so that they have a common usage.

## Building

```bash
docker build -t local/nightjar-base-envoy -f Dockerfile.envoy .
docker build -t local/nightjar-base-alpine -f Dockerfile.alpine .
```
