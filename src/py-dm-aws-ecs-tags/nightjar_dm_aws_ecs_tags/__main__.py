
"""
Entry point for the discovery map - pulls from AWS ECS tags implementation extension.
"""

import sys
from .main import main

sys.exit(main(sys.argv))
