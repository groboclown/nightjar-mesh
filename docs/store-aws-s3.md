# Data Store Implementation: AWS S3

## Usage

In the Nightjar container, set these environment variables, in addition to the [standard settings](standard-usage.md):

```bash
DATA_STORE_EXEC="python3 -m nightjar_ds_aws_s3"
NJ_DSS3_BUCKET=my-s3-bucket-name
NJ_DSS3_BASE_PATH=path/in/s3/bucket
NJ_DSS3_MAX_DOCUMENT_SIZE_MB=4
```

Details:

* `NJ_DSS3_BUCKET` - the S3 bucket to store the data in.  If this isn't given, then the data store will fail.
* `NJ_DSS3_BASE_PATH` - defaults to `nightjar-datastore`.

Like all data store extension points, this can be used as a discovery map by adding the extra arguments:

```bash
DISCOVERY_MAP_EXEC: python3 -m nightjar_ds_aws_s3 --document=discovery-map --action=fetch
```


## Implementation Details

The management of the documents is done to be as atomic and simple as possible.  As such, it manages each document under the path `/(base_path)/(document-name)/(version).data` and an accompanying file `/(base_path)/(document-name)/(version).meta`.  During document commit, there may be multiple versions present at once.  When the commit completes, all older versions are removed.  "Most recent version" is determined by the S3 date for the file.

This method has two advantages.  First, it means that the version is always on the file listing, which means no file contents need to be downloaded to discover which is the most recent.  Second, because it always writes a new file for the new version, it avoids the issue of fetching stale data (S3 provides read-after-write consistency for PUTS of new objects, and eventual consistency for overwrite PUTS and DELETES).

It has the disadvantage of making the fetch algorithm more complex, with a need to retry if a discovered version from listing ends up getting deleted before it is then fetched.  There's also an issue with multiple committers colliding with each other, and with a failure state where only one of the two files is created.  There are mitigating methods used to deal with this, but that's additional logic.
