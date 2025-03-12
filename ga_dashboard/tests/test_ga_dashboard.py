from importlib import resources

# Add the module's path:
import sys
sys.path.append('src')
# sys.path.append('testdata')
# This works if run as `pytest` from the `GA4HPCdashboard/ga_dashboard` directory.

from ga_dashboard.backend.utils import validate_args
from ga_dashboard.backend.data_sql_import import DataSQLImport, parse_string_to_number
from ga_dashboard.backend.ga_tools import GA_tools, agg_functions_from_raw, extract_data, main_backend


# Laurent: "This could an additional thing to build: a check that the cluster_info file contains all the required field (check format ?)
# And we could also do the same for the Slurm data file(s)."
def test_check_cluster_info_file(): # To test check_cluster_info_file()
    pass

def test_check_slurm_data_file(): # To test check_slurm_data_file()
    pass
# Just placeholders for now


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
        path_infrastructure_info="./samples", # This assumes pytest is called from the ga_dashboard directory.
    )

    main_backend(args)


# Debugging and testing
#
## For the backend
# 
# `sacct` can only be called from CSD3, and `sacct --allusers` can only be called with admin rights (which we don’t have on CSD3).
# So for now, the backend can be tested two different ways:
#
# - By using a single users’ `sacct` output, e.g. Loïc’s: `testdata/sacct_output_loic1.txt` which only bypasses the `sacct` call.
# This is the equivalent of `WorkloadManager.logs_raw` .
#
# - By using a simulated aggregated output (equivalent to `df_agg_X` ) containing multiple users’ data. For example,
# `testdata/df_agg_X_mockMultiUsers_1` can be used for this.
#
#
## For the frontend
#
# The frontend can use data aggregated further (1 row per user per day), e.g. `testdata/userDaily_mockMultiUsers_1.csv`
