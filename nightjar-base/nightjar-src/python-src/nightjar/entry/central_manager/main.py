
import os
import sys
import argparse
import textwrap
from ...data_stores import ENVOY_BOOTSTRAP_TEMPLATE_PURPOSE
from ...data_stores.s3 import (
    S3EnvConfig, S3Backend,
    ENV_BUCKET, ENV_BASE_PATH, AWS_REGION, AWS_PROFILE,
)
from .process import process, DEFAULT_NAME


def main() -> None:
    parser = argparse.ArgumentParser(
        prog='central_manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""Tool to upload template files into the backend data store,
for use by the nightjar centralized configurator.  Each invocation creates a new, atomic version of the templates.

These are split by:
    for namespace templates:
        namespace/(namespace_id)/(purpose)
    for service/color templates:
        service/(service_name)/(color_name)/(purpose)
    where:
        namespace_id: ID of the namespace (not the ARN), or `{1}` to be the templates for namespace IDs not explicitly declared.
        service_name: the name of the service, or `{1}` for service/colors that are not explicitly defined.
        color_name: the name of the color, or `{1}` for service/colors that are not explicitly defined.  Note that if service is the default, then only the default color is allowed.
        purpose: the file name.  The name {0} is reserved for the envoy proxy bootstrap configuration file.  This has its own special rules.
""").format(ENVOY_BOOTSTRAP_TEMPLATE_PURPOSE, DEFAULT_NAME)
    )
    parser.add_argument(
        '-b', '--backend', dest='backend', default="not given", required=True,
        help="backend data store.  Currently supports `s3`."
    )
    parser.add_argument(
        '--region', dest='aws_region', default=os.environ.get(AWS_REGION),
        help="AWS region.  Defaults to the ENV value `{0}`.".format(AWS_REGION)
    )
    parser.add_argument(
        '--profile', dest='aws_profile', default=os.environ.get(AWS_PROFILE),
        help="AWS profile, from the credentials.  Defaults to the ENV value `{0}`.".format(AWS_PROFILE)
    )
    parser.add_argument(
        '--s3-bucket', dest='s3_bucket', default=os.environ.get(ENV_BUCKET),
        help="(s3 backend only) the bucket that will store the templates.  Defaults to ENV value `{0}`".format(
            ENV_BUCKET
        )
    )
    parser.add_argument(
        '--s3-base-path', dest='s3_base_path', default=os.environ.get(ENV_BASE_PATH),
        help="(s3 backend only) the path in the bucket that the templates are placed in.  Defaults to ENV value `{0}`".format(
            ENV_BASE_PATH
        )
    )
    parser.add_argument(
        'templatedir', metavar='templatedir',
        help="""local directory containing the templates to upload."""
    )

    parsed = parser.parse_args()
    if not parsed.aws_region:
        print("You must specify --region or AWS_REGION.")
        sys.exit(1)
    if parsed.backend.strip().lower() == 's3':
        backend = S3Backend(S3EnvConfig().load({
            AWS_REGION: parsed.aws_region,
            AWS_PROFILE: parsed.aws_profile,
            ENV_BUCKET: parsed.s3_bucket,
            ENV_BASE_PATH: parsed.s3_base_path,
        }))
    else:
        print("The valid backends are `s3`.  Please specify a valid backend.")
        sys.exit(1)

    process(backend, parsed.templatedir)
