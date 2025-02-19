from importlib import resources

# Add the module's path:
import sys
sys.path.append('src')
# sys.path.append('testdata')
# This works if run as `pytest` from the `GA4HPCdashboard/ga_dashboard` directory.
# There is probably a better way than this.

from ga_dashboard.backend.utils import validate_args
from ga_dashboard.backend.data_sql_import import DataSQLImport, parse_string_to_number
from ga_dashboard.backend.ga_tools import GA_tools, agg_functions_from_raw, extract_data, main_backend


# Check that we can call our functions ok:
# Use decorators to run these.

def test_parse_string_to_number():
    assert parse_string_to_number("100") == 100
    assert parse_string_to_number("xyz") == "xyz"


# This isn't really a proper test. And, the main_backend() function calls extract_data(), which uses files not
# currently under version control (need to anonymise them before adding to git.)
def test_main_backend():
    from collections import namedtuple
    argStruct = namedtuple('argStruct',
                           'startDay endDay useCustomLogs use_mock_agg_data reportBug reportBugHere path_infrastructure_info')
    args = argStruct(
        startDay='2022-01-01',
        endDay='2023-06-30',
        useCustomLogs="", #"sacct_output_loic1.txt",
        use_mock_agg_data=True,
        reportBug=False,
        reportBugHere=False,
        path_infrastructure_info="data/ourInfrastructure/CSD3",
    )

    main_backend(args)



