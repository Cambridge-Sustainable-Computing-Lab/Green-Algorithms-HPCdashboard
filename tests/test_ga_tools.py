import argparse
import datetime
import os
import pandas as pd
import yaml

from ga_dashboard.backend.ga_tools import extract_data # , GA_tools 

# NB We assume the tests are run from the top-level GA4HPCdashboard directory.

def run_extract_data(logfile: str, clusterfile: str) -> pd.DataFrame:
    pass

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


def test_extract_data():
    """
    test the extract_data() function and dataframe
    """
   
    ns = generate_namespace('one_line_sacct_output.txt')

    ### Load cluster-specific info
    with open(os.path.join(ns.path_infrastructure_info, 'cluster_info.yaml'), "r") as stream:
        try:
            cluster_info = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    df = extract_data(ns, False, cluster_info)  #=cluster_info)

    assert len(df) == 1  # Only 1 job ran
    myseries = df.squeeze(axis=0)

    assert myseries.WallclockTimeX == datetime.timedelta(days=0, hours=0, minutes=13, seconds=31) # 0 days 00:13:31
    assert myseries.ReqMemX == 60.15
    assert myseries.PartitionX == "yew-himem"
    assert myseries.SubmitDatetimeX == datetime.datetime(2022, 11, 11, 18, 54, 33) # 2022-11-11T18:54:33 
    assert myseries.StateX == 1
    assert myseries.UIDX == "11111"
    assert myseries.UserX == "uid_1"


    ### Load fixed parameters
    #with open(ns.fixed_params_file, "r") as stream:        
    #    try:
    #        fixed_params = yaml.safe_load(stream)
    #    except yaml.YAMLError as exc:
    #        print(exc)

    # Instantiate GA_tools object - used with enrich_data()
    #GA = GA_tools(cluster_info, fixed_params)

    #df = run_extract_data('sacct_output_single_user.txt', 'ga_dashboard/data/fixed_parameters.yaml')
    #df = extract_data(ns, False, cluster_info)



def test_enrich_data():
    pass

