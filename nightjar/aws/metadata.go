package aws

import (
	"net/http"
	"io/ioutil"
)

// General functions that interact with the AWS meta-data service.
// See https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html

func GetInstanceIp() (string, error) {
	resp, gErr := http.Get("http://169.254.169.254/2018-09-24/meta-data/local-ipv4")
	if gErr != nil {
		return "", gErr
	}

	data, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}
	return string(data), nil
}
