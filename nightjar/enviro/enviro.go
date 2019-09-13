// Loads up the environment variables for use with the rest of the program.
package enviro

import (
	"os"
	"time"
	"strings"
	"strconv"
)

// PathRef contains information about a service, either inbound or outbound.
type PathRef struct {
	Id              string
	ServiceArn      *string
	Path            *string
	ContainerName   *string
	ContainerPort   uint32
	Cluster         *string
}

// EnvoyRef contains information that describes how to setup and connect to Envoy.
type EnvoyRef struct {
	AdminPort	uint32
	IngressPort	uint32 // <= 0 if not used
	EgressPort	uint32 // <= 0 if not used
	HealthCheckPath	string
	HealthCheckStatus uint32
	HealthCheckBody string
}


// ReadEgress loads the service definitions from the environment variables.
func ReadEgress() []*PathRef {
	ret := make([]*PathRef, 0)

	defaultCluster, defaultClusterOk := os.LookupEnv("CLUSTER")

	i := 1
	for {
		arnVal, arnOk := lookupIndexEnv("SERVICE_ARN_", i)
		pathVal, pathOk := lookupIndexEnv("SERVICE_PATH_", i)
		containerVal, _ := lookupIndexEnv("SERVICE_CONTAINER_", i)
		portVal := lookupIntEnv("SERVICE_PORT_", i, 0)
		clusterVal, clusterOk := lookupIndexEnv("SERVICE_CLUSTER_", i)
		if !clusterOk {
			clusterOk = defaultClusterOk
			clusterVal = &defaultCluster
		}

		if arnOk && pathOk && clusterOk {
			ret = append(ret, NewPathRef(
				arnVal, pathVal, containerVal, portVal, clusterVal,
			))
		} else {
			return ret
		}
		i += 1
	}
}


// ReadIngress loads exported, local service tasks that receive inbound traffic.
func ReadIngress() []*PathRef {
	ret := make([]*PathRef, 0)

	arnVal, arnOk := os.LookupEnv("CURRENT_SERVICE_ARN")
	clusterVal, clusterOk := os.LookupEnv("CLUSTER")
	if !arnOk || !clusterOk {
		return ret
	}

	i := 1
	for {
		nameVal, nameOk := lookupIndexEnv("TASK_NAME_", i)
		pathVal, pathOk := lookupIndexEnv("TASK_PATH_", i)
		port := lookupIntEnv("TASK_PORT_", i, 0)

		if nameOk && pathOk {
			ret = append(ret, NewPathRef(
				&arnVal, pathVal, nameVal, port, &clusterVal,
			))
		} else {
			return ret
		}
		i += 1
	}
}

// Default envoy setup values
const (
	defaultPort uint32 = 9902
)

// ReadEnvoy loads the envoy configuration information.
func ReadEnvoy() *EnvoyRef {
	ret := EnvoyRef{
		AdminPort: lookupIntEnv("ENVOY_ADMIN_PORT", -1, defaultPort),
		EgressPort: lookupIntEnv("EGRESS_LISTEN_PORT", -1, 0),
		IngressPort: lookupIntEnv("INGRESS_LISTEN_PORT", -1, 0),

	}
	return &ret
}


// ReadWaitTime reads the polling wait time.
func ReadWaitTime() time.Duration {
	return time.Duration(lookupIntEnv("WAITTIME", -1, 100))
}


func lookupIndexEnv(prefix string, index int) (*string, bool) {
	env := strings.Join([]string{prefix, strconv.Itoa(index)}, "")
	v, ok := os.LookupEnv(env)
	return &v, ok
}


func lookupIntEnv(prefix string, index int, defaultVal uint32) uint32 {
	env := prefix
	if index >= 0 {
		env = strings.Join([]string{prefix, strconv.Itoa(index)}, "")
	}
	val, ok := os.LookupEnv(env)
	if ok {
		reti, err := strconv.Atoi(val)
		if err != nil {
			return uint32(reti)
		}
	}
	return defaultVal
}


func NewPathRef(
		serviceArn *string, 
		path *string,
		containerName *string,
		containerPort uint32,
		cluster *string,
) *PathRef {
	id := strings.Join([]string{
		*serviceArn, *path, *containerName, strconv.FormatInt(int64(containerPort), 10), *cluster,
	}, "&")
	return &PathRef{
		Id: id,
		ServiceArn: serviceArn,
		Path: path,
		ContainerName: containerName,
		ContainerPort: containerPort,
		Cluster: cluster,
	}
}
