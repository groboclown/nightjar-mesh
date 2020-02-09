# About

Serverless model for the central Nightjar discovery service.  It can be triggered through various events, such as CloudWatch timers or SQS messages.

It can store data compatible with the nightjar-jookup container.

The biggest difference between the lambda and the docker images is the location of the configuration files.  The lambda cannot support the file versions.
