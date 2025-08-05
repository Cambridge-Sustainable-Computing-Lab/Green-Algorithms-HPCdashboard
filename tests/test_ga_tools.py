import argparse
import datetime
import os
import pandas as pd
import pytest


from ga_dashboard.backend.ga_tools import GA_tools, extract_data, enrich_data, summarise_data

from ga_dashboard.backend.utils import get_cluster_info, get_fixed_params

# Tests for the functions in ga_tools.py

# NB We assume the tests are run from the top-level GA4HPCdashboard directory.

# Utility function
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


# Utility function
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


def test_extract_enrich_data_one_job():
    """
    Test the extract_data() and enrich_data() functions and dataframe
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
    #sacct_logfile = "batched_sacct_output.txt"
    # We use this later, below.
    raw_df = pd.read_csv('tests/testdata/batched_sacct_output.txt', sep='|')

    ns = generate_namespace("batched_sacct_output.txt")
    cluster_info = get_cluster_info(ns, 'cluster_info.yaml')
    extracted_df = extract_data(ns, True, cluster_info)
    assert len(extracted_df) == 5 # There are 5 jobs in the file, including two batched ones.
                                  # Job 8325013 is 4th (i.e. index=3)

    # memory check (on a different job) for completeness
    my_series = extracted_df.iloc[1]
    assert my_series.ReqMemX == 3.37  # 3370 MB = 3.37 GB

    # OK, now we will compare this series for job 8325013 with what we expect
    my_series = extracted_df.iloc[3]

    # pytest.set_trace()
    # UID|User|JobID|JobName|Submit|Elapsed|Partition|NNodes|NCPUS|TotalCPU|CPUTime|ReqMem|MaxRSS|WorkDir|State|Account|AllocTRES
    # 47892|uid_2|8325013|hellojob|2025-04-14T16:30:21|00:00:06|yew|1|1|00:00.262|00:00:06|3370M||/home/uid_2|COMPLETED|group_1-sl3-cpu|billing=1,cpu=1,mem=3370M,node=1
    # ||8325013.batch|batch|2025-04-15T04:53:39|00:00:06||1|1|00:00.261|00:00:06||0||COMPLETED|group_1-sl3-cpu|cpu=1,mem=3370M,node=1
    # ||8325013.extern|extern|2025-04-15T04:53:39|00:00:06||1|1|00:00:00|00:00:06||0||COMPLETED|group_1-sl3-cpu|billing=1,cpu=1,mem=3370M,node=1
    my_first_batched_df = raw_df[raw_df.JobID.str.startswith('8325013')]
    assert len(my_first_batched_df) == 3

    # Now we can check that the results we get back from extract_data() are correct,
    # with reference to the raw_df we read in directly from the logfile.

    # NB It may be better to move this to test_slurm.py, as clean_logs_df() is in slurm.py

    # The submit date is taken as the minimum of the 3 with this common JobID
    # by clean_logs_df() in slurm.py, called by extract_data()
    submit_date = min(my_first_batched_df.Submit)
    timestamp = datetime.datetime.strptime(submit_date, "%Y-%m-%dT%H:%M:%S")
    assert(my_series.SubmitDatetimeX == timestamp)
    # AssertionError: assert Timestamp('2025-04-14 16:30:21') == '2025-04-14T16:30:21'
    # lambda x: datetime.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S"))

    assert my_series.PartitionX == "yew"
    assert my_series.ReqMemX == 3.37
    #assert my_series.UsedMem_ == 3.37 WallclockTimeX
    assert my_series.WallclockTimeX == datetime.timedelta(days=0, hours=0, minutes=0, seconds=6)
    assert my_series.UIDX == "47892"
    assert my_series.UserX == "uid_2"
    assert my_series.StateX == 1
    assert my_series.PartitionTypeX == "CPU"
    assert my_series.TotalCPUtime2useX == datetime.timedelta(milliseconds=262)
    assert my_series.TotalGPUtime2useX == datetime.timedelta(0)
    assert my_series.CPUhoursChargedX == 0.0016666666666666668  # 6 seconds
    assert my_series.GPUhoursChargedX == 0.

    # MaxRSS = None for this job.
    # granularity of memory request = 6GB
    assert my_series.NeededMemX == 3.37 # per clean_UsedMem() in slurm.py (No MaxRSS value)
    assert my_series.memOverallocationFactorX == 1.
    #pytest.set_trace()  # run with pytest --pdb


    # Load fixed parameters
    fixed_params = get_fixed_params(ns, 'fixed_parameters.yaml')

    GA = GA_tools(cluster_info, fixed_params)

    users_df = get_users_df(ns, 'hpc_users_list.csv')
    df2 = enrich_data(extracted_df, fixed_params, users_df, GA)
    assert len(df2) == 5


def test_enrich_data():
    pass


def test_summarise_data():
    pass


def test_clean_logs():
    pass

# I want to test that jobs are aggregated correctly
# hierachical aggregation in pandas
