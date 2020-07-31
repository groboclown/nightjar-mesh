
"""
Entry point for the discovery map - pulls from AWS ECS tags implementation extension.
"""

import sys
from nightjar_dm_aws_ecs_tags.main import main

sys.exit(main(sys.argv))
