package main

import (
    "flag"

    "github.com/groboclown/nightjar-mesh/nightjar"
    "github.com/groboclown/nightjar-mesh/nightjar/util"
)

func main() {
    mode := flag.String("mode", "poll",
        "Alters the operational mode of the program.  Options are one of: " +
        "'poll': Poll for changes in the AWS ECS configuration; " +
        "'aws-check': Report the current ECS configuration based on the environment variables and quit; " +
        "'envoy-check': Report the current Envoy configuration based on the environment variables and quit.",
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

    if *mode == "poll" {
        nightjar.Poll()
    } else if *mode == "aws-check" {
        nightjar.AwsCheck()
    } else if *mode == "envoy-check" {
        nightjar.EnvoyCheck()
    } else {
        util.Fatal("Invalid `mode` flag value:", mode)
    }
}
