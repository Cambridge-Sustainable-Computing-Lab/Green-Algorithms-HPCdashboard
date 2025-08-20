import argparse
import datetime
import os
import pandas as pd
import pytest
import yaml

from ga_dashboard.backend.ga_tools import GA_tools, extract_data, enrich_data, summarise_data

# NB We assume the tests are run from the top-level GA4HPCdashboard directory.

#def run_extract_data(logfile: str, clusterfile: str) -> pd.DataFrame:
#    pass

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

    # Get path to testdata/ subdir
    ns.path_infrastructure_info = os.path.join(cwd, 'tests/testdata')
    #ns.useCustomLogs = os.path.join(ns.path_infrastructure_info, 'sacct_output_single_user.txt')
    ns.useCustomLogs = os.path.join(ns.path_infrastructure_info, logfile)
    print("using " + ns.useCustomLogs )

    return ns


<<<<<<< HEAD
def get_yaml_object(infile: str) -> object:
=======
def get_cluster_info(ns: argparse.Namespace, info_file: str) -> object:
>>>>>>> parent of 223b2db (Removed duplicate files.)
    """
    Get the YAML object representation of a .yaml file.
    :param infile: [str] Name of input file, e.g., 'cluster_info.yaml' or 'fixed_parameters.yaml'
    :return: [object] The object representation.
    """
<<<<<<< HEAD
    with open(infile, "r") as stream:
=======
    with open(os.path.join(ns.path_infrastructure_info, info_file), "r") as stream:
>>>>>>> parent of 223b2db (Removed duplicate files.)
        try:
            object_rep = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
<<<<<<< HEAD
    return object_rep    
=======
    return cluster_info


def get_fixed_params(ns: argparse.Namespace, fp_file: str) -> object:
    """
    Get the YAML object representation of the fixed parameters file.
    :param ns: [argparse.Namespace] Namespace representing the command-line arguments.
    :param fp_file: [str] Name of fixed params file, e.g., 'cluster_info.yaml'
    :return: [argparse.Namespace] The populated Namespace (args) object.
    """
    with open(os.path.join(ns.path_infrastructure_info, fp_file), "r") as stream:
        try:
            fixed_params = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return fixed_params


#def get_users_df(ns: argparse.Namespace, user_list_file: str) -> pd.DataFrame:
#    """
#    Get the Pandas DataFrame representing the HPC users in user_list_file.
#    :param ns: [argparse.Namespace] Namespace representing the command-line arguments.
#    :param user_list_file: [str] Name of users file, e.g., 'sample_user_list.csv'
#    :return: [pd.DataFrame] The data frame object.
#    """
#    try:
#        users_df = pd.read_csv(os.path.join(ns.path_infrastructure_info, user_list_file))
#    except FileNotFoundError:
#        #if has_slurmAdmin:
#        #    raise ValueError("No user data available.")
#        users_df = None
#    return users_df
>>>>>>> parent of 223b2db (Removed duplicate files.)



def get_users_df(user_list_file: str) -> pd.DataFrame:
    """
    Get the Pandas DataFrame representing the HPC users in user_list_file.
    :param user_list_file: [str] Name of users file, e.g., 'sample_user_list.csv'
    :return: [pd.DataFrame] The data frame object.
    """
    try:
        users_df = pd.read_csv(user_list_file)
    except FileNotFoundError:
        #if has_slurmAdmin:
        #    raise ValueError("No user data available.")
        users_df = None
    return users_df



def test_extract_data():
    """
    Test the extract_data() function and dataframe
    """   
    logfile = "tests/testdata/one_line_sacct_output.txt"
    #ns = generate_namespace('one_line_sacct_output.txt')
<<<<<<< HEAD
    #ns = generate_namespace("tests/testdata/one_line_sacct_output.txt")

    cluster_info = get_yaml_object('docs/templates/cluster_info.yaml')

=======
    ns = generate_namespace("tests/testdata/one_line_sacct_output.txt")
    cluster_info = get_cluster_info(ns, 'cluster_info.yaml')
>>>>>>> parent of 223b2db (Removed duplicate files.)
    config_data = {}
    config_data['useCustomLogs'] = logfile
    df = extract_data(config_data, True, cluster_info)

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
<<<<<<< HEAD
    fixed_params = get_yaml_object('ga_dashboard/data/fixed_parameters.yaml')
=======
    fixed_params = get_fixed_params(ns, 'fixed_parameters.yaml')
>>>>>>> parent of 223b2db (Removed duplicate files.)

    GA = GA_tools(cluster_info, fixed_params)
    
    df2 = enrich_data(df, fixed_params, None, GA)
    series2 = df2.squeeze(axis=0) 
    assert myseries.WallclockTimeX == series2.WallclockTimeX
    assert myseries.PartitionX == series2.PartitionX
    # etc ... all should be the same
    series2 = None

    users_df = get_users_df('docs/templates/sample_user_list.csv')
    df2 = enrich_data(df, fixed_params, users_df, GA)
    assert len(df2) == 1
    series2 = df2.squeeze(axis=0) 
    assert series2.energy_failedJobs == 0
    assert series2.energy_GPUs == 0
    assert series2.energy_CPUs == pytest.approx(0.010588055555555557)
    assert series2.carbonFootprint_failedJobs == 0
    #assert series2.carbonFootprint == 
    # (row.energy_CPUs +  row.energy_GPUs + row[f'energy_memory{suffix}']) * self.cluster_info['PUE'] # in kWh

    summary_stats = summarise_data(df2)
    print("SUMMARY STATS")
    print(summary_stats["groupActivity"])

def test_enrich_data():
    pass

