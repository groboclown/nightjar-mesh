
import os
import sys
import argparse
import textwrap
from ...data_stores.s3 import (
    S3EnvConfig, S3Backend,
    ENV_BUCKET, ENV_BASE_PATH, AWS_REGION, AWS_PROFILE,
)
from .file_mgr import TEMPLATE_DESCRIPTION_FILENAME, CONFIG_DESCRIPTION_FILENAME
from .push_templates import push_templates
from .pull_files import pull_generated_files, pull_templates


ACTION_NAME__PUSH_TEMPLATES = 'push-templates'
ACTION_NAME__PULL_TEMPLATES = 'pull-templates'
ACTION_NAME__PULL_CONFIGURED = 'pull-configured'


def main() -> None:
    parser = argparse.ArgumentParser(
        prog='central_manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""Tool to upload template files into the backend data store, and read them back.
For use by the nightjar centralized configurator.
""")
    )
    parser.add_argument(
        '-b', '--backend', dest='backend', default="not given", required=True,
        choices=['s3'],
        help="backend data store.  Currently supports only `s3`."
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
        help=(
            "(s3 backend only) the path in the bucket that the templates are placed in.  Defaults to ENV value `{0}`"
            .format(
                ENV_BASE_PATH
            )
        )
    )

    # ---------------------------------------------
    # Actions
    parser_command = parser.add_subparsers(
        dest='action_name',
        title="actions",
        description="valid actions",
        help="help for each action",
    )

    # push-template
    parser_push_template = parser_command.add_parser(
        ACTION_NAME__PUSH_TEMPLATES,
        help=("Push templates in the `source` directory up to the data store.  All the contents are considered a single "
              "unit, and will be come the next version of the templates.  Any existing templates in the data store "
              "will no longer be used.  Each child directory in `source` must contain a "
              "file named {0}, which must be a json-formatted dictionary with keys depending on the kind of template "
              "this directory represents.  For namespaces, it must have `\"type\":\"namespace\"`, and the keys "
              "`namespace` (`null` value for the default value) and `is-public` (a boolean which can be `null` for "
              "the default value).  For service-colors, it must have `\"type\":\"service-color\", and the keys "
              "`namespace`, `service`, and `color` (null values mean default).".format(TEMPLATE_DESCRIPTION_FILENAME)),
    )
    parser_push_template.add_argument(
        'source',
        help="local directory containing the templates to upload.",
    )

    # pull templates
    parser_pull_templates = parser_command.add_parser(
        ACTION_NAME__PULL_TEMPLATES,
        help="Pull the latest version of the templates from the data store into the output directory.  These are "
             "collected into directories with auto-assigned names, and an additional file named {0} which describes "
             "the downloaded files.".format(TEMPLATE_DESCRIPTION_FILENAME),
    )
    parser_pull_templates.add_argument(
        'output',
        help="local directory to store the downloaded template files.",
    )

    # pull configured
    parser_pull_configured = parser_command.add_parser(
        ACTION_NAME__PULL_CONFIGURED,
        help="Pull the latest version of the configured files from the data store into the output directory.  Used "
             "to verify the generated content of the envoy proxy files.  The files are "
             "collected into directories with auto-assigned names, and an additional file named {0} which describes "
             "the downloaded files.".format(TEMPLATE_DESCRIPTION_FILENAME),
    )
    parser_pull_configured.add_argument(
        'output',
        help="local directory to store the downloaded configured files.",
    )

    # # clean templates
    # parser_clean_templates = parser_command.add_parser(
    #     'clean-templates',
    #     help="Clean old versions of the templates that are no longer being used."
    # )
    #
    # # clean configured
    # parser_clean_configured = parser_command.add_parser(
    #     'clean-configured',
    #     help="Clean old versions of the configured files that are no longer being used."
    # )
    #
    # # clean everything
    # parser_clean_all = parser_command.add_parser(
    #     'clean-all',
    #     help="Clean the old versions of all the files."
    # )

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

    if parsed.action_name == ACTION_NAME__PUSH_TEMPLATES:
        push_templates(backend, parsed.source)
    elif parsed.action_name == ACTION_NAME__PULL_TEMPLATES:
        pull_templates(backend, parsed.output)
    elif parsed.action_name == ACTION_NAME__PULL_CONFIGURED:
        pull_generated_files(backend, parsed.output)
    else:
        print("Unknown action `{0}`.  See the help for details.".format(parsed.action_name))
        sys.exit(1)
