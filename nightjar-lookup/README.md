# About

The Envoy Proxy implementation that polls S3 for the configuration.

The container knows about just one network ID OR one service ID (it's the same from an implementation standpoint).  The container reads from the s3 bucket / path into a directory, then moves that into the Envoy paths.

The container will require read access to a limited subset of S3 bucket / paths.
