package main

import (
	"flag"

	"github.com/groboclown/nightjar-mesh/nightjar"
	"github.com/groboclown/nightjar-mesh/nightjar/util"
)

func main() {
	mode := flag.String("mode", "serve",
		"Alters the operational mode of the program.  Options are one of: " +
		"'serve': Run as a control-mesh server for the Envoy proxy; " +
		"'aws-check': Report the current ECS configuration based on the environment variables and quit; ",
	)
	debug := flag.Bool("d", false, "debug logging")
	verbose := flag.Bool("v", false, "verbose logging")
	flag.Parse()

	if *verbose {
		util.SetLogLevel(util.VERBOSE)
	}
	if *debug {
		util.SetLogLevel(util.DEBUG)
	}

	if *mode == "serve" {
		nightjar.Serve()
	} else if *mode == "aws-check" {
		nightjar.AwsCheck()
	} else {
		util.Fatal("Invalid `mode` flag value:", mode)
	}
}
