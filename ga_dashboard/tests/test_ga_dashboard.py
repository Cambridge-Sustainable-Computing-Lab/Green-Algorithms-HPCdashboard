from importlib import resources

# Add the module's path:
import sys
sys.path.append('src')
# This works if run as `pytest` from the `GA4HPCdashboard/ga_dashboard` directory.

from ga_dashboard.backend.utils import validate_args

