package nightjar

import (
    "github.com/groboclown/nightjar-mesh/nightjar/enviro"
    "github.com/groboclown/nightjar-mesh/nightjar/envoy"
    "github.com/groboclown/nightjar-mesh/nightjar/util"
)


func EnvoyCheck() {
    envoySvc := envoy.NewEnvoySvc(enviro.ReadEnvoy(), func (err error) {
        util.Fatal("Envoy problem:", err)
    })
	if envoySvc == nil {
		util.Fatal("Could not create envoy service connector.")
	}
}
