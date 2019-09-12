package enviro_test

import (
    "os"
    "testing"
    "strings"
    "strconv"
)


func TestReadServices_1(t *testing.T) {
    unset_all()
    set_service(1, "", "p", "c")
    got := ReadServices()
    if len(got) != 0 {
        t.Errorf("no arn incorrectly generated a service")
    }
}


func set_service(index int, arn string, path string, cluster string) {
    set_env(concat("SERVICE_ARN_", index), arn)
    set_env(concat("SERVICE_PATH_", index), path)
    set_env(concat("SERVICE_CLUSTER_", index), cluster)
}


func set_task(index int, name string, path string) {
    set_env(concat("TASK_NAME_", index), name)
    set_env(concat("TASK_PATH_", index), path)
}

func set_global(cluster string, arn string) {
    set_env("CLUSTER", cluster)
    set_env("CURRENT_SERVICE_ARN", arn)
}

func set_env(key string, value string) {
    if len(value) > 0 {
        os.Unsetenv(key)
    } else {
        os.Setenv(key, value)
    }
}


func unset_all() {
    os.Unsetenv("CLUSTER")
    os.Unsetenv("CURRENT_SERVICE_ARN")

    for i := 1; i <= 4; i+= 1 {
        os.Unsetenv(concat("SERVICE_ARN_", i))
        os.Unsetenv(concat("SERVICE_PATH_", i))
        os.Unsetenv(concat("SERVICE_CLUSTER_", i))
        os.Unsetenv(concat("TASK_NAME_", i))
        os.Unsetenv(concat("TASK_PATH_", i))
    }
}

func concat(pref string, index int) string {
    return strings.Join([]string{pref, strconv.Itoa(index)}, "")
}
