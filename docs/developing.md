# Developer's Guide


## Environment Setup

You can develop in Windows, but this guide is for Linux and OSX folks.  Translate as necessary.

Ensure you have GoLang at version 1.15 or better.  Ensure you have [glide](https://glide.sh/) installed.

Pull down the source from GitHub into your Go working directory.  Here, it's assuming you're using the official repo path, but you can use a personal fork if necessary.

```bash
$ git clone https://github.com/groboclown/nightjar-mesh $GOPATH/src/github.com/groboclown/nightjar-mesh
```

And yank down all the dependencies.

```bash
$ cd $GOPATH/src/github.com/groboclown/nightjar-mesh
$ glide update
```


## Local Build

```bash
$ cd $GOPATH/src/github.com/groboclown/nightjar-mesh
$ go build -o dist/nightjar-mesh && go test
```

## Testing in AWS

To test the AWS portion in AWS, you'll need to upload the executable to AWS.  Because of the size of the binary, we recommend using `rsync` to only upload the differences.  You'll need to make sure that `rsync` is installed both locally and on the remote EC2 instance.

```bash
$ rsync -av -e "ssh -i ~/.aws/my-login.pem" dist/nightjar-mesh ec2-user@123.45.67.89:.
```
