package enviro

import (
    "os"
    "time"
    "strings"
    "strconv"
)

type PathRef struct {
    Id              string
    ServiceArn      *string
    Path            *string
    ContainerName   *string
    ContainerPort   int64
    Cluster         *string
}

type EnvoyRef struct {
    Hostname        string
    Port            int64
}

/**
 * Read the service definitions from the environment variables.
 */
func ReadEgress() []*PathRef {
    ret := make([]*PathRef, 0)

    defaultCluster, defaultClusterOk := os.LookupEnv("CLUSTER")

    i := 1
    for {
        arnVal, arnOk := lookup_index_env("SERVICE_ARN_", i)
        pathVal, pathOk := lookup_index_env("SERVICE_PATH_", i)
        containerVal, _ := lookup_index_env("SERVICE_CONTAINER_", i)
        portVal := lookup_int_env("SERVICE_PORT_", i, -1)
        clusterVal, clusterOk := lookup_index_env("SERVICE_CLUSTER_", i)
        if !clusterOk {
            clusterOk = defaultClusterOk
            clusterVal = &defaultCluster
        }

        if arnOk && pathOk && clusterOk {
            ret = append(ret, mk_pathref(
                arnVal, pathVal, containerVal, portVal, clusterVal,
            ))
        } else {
            return ret
        }
        i += 1
    }
}


/**
 * Read the exported, local service tasks that receive inbound traffic.
 */
func ReadIngress() []*PathRef {
    ret := make([]*PathRef, 0)

    arnVal, arnOk := os.LookupEnv("CURRENT_SERVICE_ARN")
    clusterVal, clusterOk := os.LookupEnv("CLUSTER")
    if !arnOk || !clusterOk {
        return ret
    }

    i := 1
    for {
        nameVal, nameOk := lookup_index_env("TASK_NAME_", i)
        pathVal, pathOk := lookup_index_env("TASK_PATH_", i)
        port := lookup_int_env("TASK_PORT_", i, -1)

        if nameOk && pathOk {
            ret = append(ret, mk_pathref(
                &arnVal, pathVal, nameVal, port, &clusterVal,
            ))
        } else {
            return ret
        }
        i += 1
    }
}

const DEFAULT_HOSTNAME string = "localhost"
const DEFAULT_PORT int64 = 9901

func ReadEnvoy() *EnvoyRef {
    ret := EnvoyRef{ Hostname: DEFAULT_HOSTNAME, Port: DEFAULT_PORT }

    hostVal, hostOk := os.LookupEnv("ENVOY_CONTAINER_NAME")
    if hostOk {
        ret.Hostname = hostVal
    }
    ret.Port = lookup_int_env("ENVOY_ADMIN_PORT", -1, DEFAULT_PORT)
    return &ret
}


func ReadWaitTime() time.Duration {
    return time.Duration(lookup_int_env("WAITTIME", -1, 100))
}


func lookup_index_env(prefix string, index int) (*string, bool) {
    env := strings.Join([]string{prefix, strconv.Itoa(index)}, "")
    v, ok := os.LookupEnv(env)
    return &v, ok
}


func lookup_int_env(prefix string, index int, defaultVal int64) int64 {
    env := prefix
    if index >= 0 {
        env = strings.Join([]string{prefix, strconv.Itoa(index)}, "")
    }
    val, ok := os.LookupEnv(env)
    if ok {
        reti, err := strconv.Atoi(val)
        if err != nil {
            return int64(reti)
        }
    }
    return defaultVal
}



func mk_pathref(
        serviceArn *string, 
        path *string,
        containerName *string,
        containerPort int64,
        cluster *string,
) *PathRef {
    id := strings.Join([]string{
        *serviceArn, *path, *containerName, strconv.FormatInt(containerPort, 10), *cluster,
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
