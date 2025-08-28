import pytest

# This works if run as `pytest` from the `GA4HPCdashboard` directory.

from ga_dashboard.backend.data_sql_import import parse_string_to_number # , DataSQLImport
from ga_dashboard.backend.ga_tools import main_backend # GA_tools, extract_data, agg_functions_from_raw,


# set up and tear down:
# https://pytest-with-eric.com/pytest-best-practices/pytest-setup-teardown/

# A database test should use a different instance of the database, so we don't ruin real data!

# Depending on the number of tests, we might want multiple test files, e.g. one per module.

# Laurent: "This could an additional thing to build: a check that the cluster_info file contains all the required field (check format ?)
# And we could also do the same for the Slurm data file(s)."
def test_check_cluster_info_file(): # To test check_cluster_info_file()
    pass

def test_check_slurm_data_file(): # To test check_slurm_data_file()
    pass
# Just placeholders for now

FIXED_PARAMS_FILE = "ga_dashboard/data/fixed_parameters.yaml"
CLUSTER_INFO_FILE = "configuration/examples/cluster_info__demo.yaml"


# parse_string_to_number()
@pytest.mark.parametrize( "a, expected",  
    [  
        ("100", 100),  
        ("xyz", "xyz"),
        ("100.00001", 100.00001)  
    ],)  
def test_parse_string_to_number(a, expected):
    assert parse_string_to_number(a) == expected



# This isn't really a proper test.
def test_main_backend():

    config_data = {}

    config_data['startDay'] = '2022-01-01'
    config_data['endDay'] = '2023-06-30'
    config_data['useCustomLogs'] = "tests/testdata/sacct_output_single_user.txt"
    config_data['use_mock_agg_data'] = False
    config_data['reportBug'] = False
    config_data['reportBugHere'] = False
    config_data['path_infrastructure_info'] = "ga_dashboard/samples"
    config_data['fixed_params_file'] = "ga_dashboard/data/fixed_parameters.yaml"
    config_data['cluster_info_file'] = "configuration/examples/cluster_info__demo.yaml"
    config_data['dashboard_users_file'] = "configuration/examples/user_list__demo.csv"

    main_backend(config_data) 


# Debugging and testing
#
## For the backend
# 
# `sacct` can only be called from CSD3, and `sacct --allusers` can only be called with admin rights (which we don’t have on CSD3).
# So for now, the backend can be tested two different ways:
#
# - By using a single users’ `sacct` output, e.g. Loïc’s: `tests/testdata/sacct_output_single_user.txt` which only bypasses the `sacct` call.
# This is the equivalent of `WorkloadManager.logs_raw` .
#
# - By using a simulated aggregated output (equivalent to `df_agg_X` ) containing multiple users’ data. For example,
# `tests/testdata/extracted_multi_users.csv` can be used for this.
#
#
## For the frontend
#
# The frontend can use data aggregated further (1 row per user per day), e.g. `tests/testdata/aggregated_multi_users.csv`
