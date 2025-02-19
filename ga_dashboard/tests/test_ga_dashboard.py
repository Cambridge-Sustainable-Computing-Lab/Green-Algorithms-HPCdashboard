from importlib import resources

# Add the module's path:
import sys
sys.path.append('src')
# This works if run as `pytest` from the `GA4HPCdashboard/ga_dashboard` directory.

from ga_dashboard.backend.utils import validate_args
from ga_dashboard.backend.data_sql_import import DataSQLImport, parse_string_to_number
from ga_dashboard.backend.ga_tools import GA_tools

def test_parse_string_to_number():
    assert parse_string_to_number("100") == 100



