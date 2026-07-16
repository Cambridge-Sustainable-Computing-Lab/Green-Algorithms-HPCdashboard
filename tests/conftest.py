# ------------------------------------------------------------------
# This file contains pytest fixtures (test configurations). It consists of fixtures that are to be used across multiple test files.
# These fixtures are automatically discovered by pytest and can be used in any test file without explicit import.
# 
# A fixture is the ready-made setup (or known-correct example) a test uses, so it need not be built fresh every time.
# ------------------------------------------------------------------

import pytest

@pytest.fixture
def config_data():
    return {
        "startDay": "2026-01-01",
        "endDay": "2026-04-01",
        "useCustomLogs": "tests/testdata/slurm_logs_many_cases.csv",
        "skip_db_overwrite": False,
        "db_name": "ga_dev",
        "db_host": "localhost",
        "db_port": 5432,
        "db_user": "postgres",
        "db_password": "temppass",
        "dashboard_users_file": "tests/testconfig/test_user_list.csv",
        "fixed_params_file": "tests/testconfig/test_fixed_params.yaml",
        "cluster_info_file": "tests/testconfig/test_cluster_config.yaml",
    }