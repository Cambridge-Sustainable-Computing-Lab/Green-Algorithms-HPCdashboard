import argparse
import datetime
import os
import pandas as pd
import pytest


from ga_dashboard.backend.ga_tools import GA_tools, extract_data, enrich_data, summarise_data

from ga_dashboard.backend.utils import get_cluster_info, get_fixed_params

# NB We assume the tests are run from the top-level GA4HPCdashboard directory.


def generate_namespace(logfile: str) -> argparse.Namespace:
    """
    Generates and populates an argparse.Namespace object, simulating command-line arguments.

    :param logfile: [str] The name of the sacct output file to use, e.g., 'sacct_output_single_user.txt'.
    :return: [argparse.Namespace] The populated Namespace (args) object.
    """
    ns = argparse.Namespace()
    ns.use_mock_agg_data = False
    ns.reportBug = False
    ns.reportBugHere = False

    cwd = os.getcwd()
    print("cwd is " + cwd) # Hopefully the GA4HPCdashboard dir

    # Get path to samples/subdir
    ns.path_infrastructure_info = os.path.join(cwd, 'tests/testdata')
    #ns.useCustomLogs = os.path.join(ns.path_infrastructure_info, 'sacct_output_single_user.txt')
    ns.useCustomLogs = os.path.join(ns.path_infrastructure_info, logfile)
    print("using " + ns.useCustomLogs )

    return ns


def get_users_df(ns: argparse.Namespace, user_list_file: str) -> pd.DataFrame:
    """
    Get the Pandas DataFrame representing the HPC users in user_list_file.
    :param ns: [argparse.Namespace] Namespace representing the command-line arguments.
    :param user_list_file: [str] Name of HPC users file, e.g., 'hpc_users_list.csv'
    :return: [pd.DataFrame] The data frame object.
    """
    try:
        users_df = pd.read_csv(os.path.join(ns.path_infrastructure_info, user_list_file))
    except FileNotFoundError:
        #if has_slurmAdmin:
        #    raise ValueError("No user data available.")
        users_df = None
    return users_df


def test_extract_data_one_job():
    """
    Test the extract_data() function and dataframe
    """   
    ns = generate_namespace('one_line_sacct_output.txt')
    cluster_info = get_cluster_info(ns, 'cluster_info.yaml')
    df = extract_data(ns, True, cluster_info)

    assert len(df) == 1  # Only 1 job ran
    myseries = df.squeeze(axis=0) # Convert the one-item dataframe into a pandas series
    assert myseries.WallclockTimeX == datetime.timedelta(days=0, hours=0, minutes=13, seconds=31) # 0 days 00:13:31
    assert myseries.ReqMemX == 60.15
    assert myseries.PartitionX == "yew-himem"
    assert myseries.SubmitDatetimeX == datetime.datetime(2022, 11, 11, 18, 54, 33) # 2022-11-11T18:54:33 
    assert myseries.StateX == 1
    assert myseries.UIDX == "11111"
    assert myseries.UserX == "uid_1"

    # Load fixed parameters
    fixed_params = get_fixed_params(ns, 'fixed_parameters.yaml')

    GA = GA_tools(cluster_info, fixed_params)
    
    df2 = enrich_data(df, fixed_params, None, GA)
    series2 = df2.squeeze(axis=0) 
    assert myseries.WallclockTimeX == series2.WallclockTimeX
    assert myseries.PartitionX == series2.PartitionX
    assert myseries.SubmitDatetimeX == series2.SubmitDatetimeX
    # etc ... all should be the same
    series2 = None

    users_df = get_users_df(ns, 'hpc_users_list.csv')
    df2 = enrich_data(df, fixed_params, users_df, GA)
    assert len(df2) == 1
    series2 = df2.squeeze(axis=0) 
    assert series2.energy_failedJobs == 0
    assert series2.energy_GPUs == 0
    assert series2.energy_CPUs == pytest.approx(0.010588055555555557)
    assert series2.carbonFootprint_failedJobs == 0
    #assert series2.carbonFootprint == 
    # (row.energy_CPUs +  row.energy_GPUs + row[f'energy_memory{suffix}']) * self.cluster_info['PUE'] # in kWh

    summary_stats = summarise_data(df2, ns)
    print("SUMMARY STATS")
    print(summary_stats["groupActivity"])



def test_extract_batched_data():
    '''
    Test extract_data() on some batched data.
    '''
    ns = generate_namespace('batched_sacct_output.txt')
    cluster_info = get_cluster_info(ns, 'cluster_info.yaml')
    df = extract_data(ns, True, cluster_info)
    assert len(df) == 5

    my_series = df.iloc[1]
    assert my_series.ReqMemX == 3.37  # 3370 MB = 3.37 GB

    #my_first_batched_df = df[df.Submit.str.startswith('2025-04-14')]  # 4 jobs.
    #my_second_batched_df = df[df.Submit.str.startswith('2025-04-16')]  # Just one job

    # Load fixed parameters
    fixed_params = get_fixed_params(ns, 'fixed_parameters.yaml')

    GA = GA_tools(cluster_info, fixed_params)

    users_df = get_users_df(ns, 'hpc_users_list.csv')
    df2 = enrich_data(df, fixed_params, users_df, GA)
    assert len(df2) == 5

    # Now drill into the


def test_enrich_data():
    pass


def test_summarise_data():
    pass


def test_clean_logs():
    pass

