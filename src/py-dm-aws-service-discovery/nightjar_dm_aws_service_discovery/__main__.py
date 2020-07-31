
"""
Entry point for the discovery map - pulls from AWS Service Discovery implementation extension.
"""

import sys
from nightjar_dm_aws_service_discovery.main import main

sys.exit(main(sys.argv))
