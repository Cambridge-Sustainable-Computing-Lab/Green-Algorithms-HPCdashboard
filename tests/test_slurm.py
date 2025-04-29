import argparse
import datetime
from io import BytesIO
from ga_dashboard.backend.workload_manager.slurm import Helpers_WM, WorkloadManager
import pandas as pd
import pytest

FIXED_PARAMS_FILE = "ga_dashboard/data/fixed_parameters.yaml"
CLUSTER_INFO_FILE = "ga_dashboard/samples/cluster_info.yaml"
SINGLE_USER_SACCT_FILE = "ga_dashboard/samples/sacct_output_single_user.txt"

# Test Helpers_WM.convert_to_GB()
@pytest.mark.parametrize( "memory, unit, expected",  
    [   
        (1_000_000_000, 'M', 1_000_000),
        (350e9, 'M', 350e6),
        (1.2e9, 'K', 1.2e3)
    ],)  
def test_convert_to_GB(memory, unit, expected):
    HWM = Helpers_WM(None)
    assert HWM.convert_to_GB(memory, unit) == expected


# Test Helpers_WM.calc_ReqMem()
# Examples of completed, timeout, failed, and cancelled jobs
# UID|User|JobID|JobName|Submit|Elapsed|Partition|NNodes|NCPUS|TotalCPU|CPUTime|ReqMem|MaxRSS|WorkDir|State|Account|AllocTRES
# 11111|uid_1|62833615|Seq_b02T|2022-06-17T11:19:40|03:27:37|oak|1|32|00:00:00|4-14:43:44|250G||/home/uid_1/a/b/c|COMPLETED|group_1-sl3-gpu|billing=32,cpu=32,gres/gpu=1,mem=250G,node=1
# 11111|uid_1|55176141|CPU-4ch|2022-02-11T19:11:21|04:00:25|ash-himem|1|1|00:00:00|04:00:25|6760M||/home/uid_1|TIMEOUT|group_1-sl2-cpu|billing=1,cpu=1,mem=6760M,node=1
# 11111|uid_1|57365466|Hyb_b01T|2022-03-20T12:54:43|00:07:12|oak|1|32|00:00:00|03:50:24|250G||/home/uid_1/a/b/c|FAILED|group_1-sl2-gpu|billing=32,cpu=32,gres/gpu=1,mem=250G,node=1
# 11111|uid_1|62064000|testPart|2022-05-31T10:16:57|00:00:00|beech|1|0|00:00:00|00:00:00|13680M||/home/uid_1|CANCELLED by 11111|group_1-sl3-cpu|
#
# Only one job ran on this day:
# 11111|uid_1|7611224|somejob_P|2022-11-11T18:54:33|00:13:31|yew-himem|1|5|00:00:00|01:07:35|60150M||another/path|COMPLETED|group_1-sl2-cpu|billing=5,cpu=5,mem=60150M,node=1
#
# with open( "ga_dashboard/samples/sacct_output_single_user.txt", 'rb') as f:
#...     logs_raw = f.read()
# logs_df = pd.read_csv(BytesIO(logs_raw), sep="|", dtype='str') # data frame
# select rows with job id 57365635
# s = logs_df[logs_df.JobID=="57365635"]   # DANGER can be > 1 match if job ids reused. It's  still a dataframe 
# s2 = logs_df.iloc[10] is a pandas Series
# >>> s2["CPUTime"]
# '03:54:40'
#
# Select 1 item - as df mydf = logs_df[logs_df.JobID == "7611224"]
# series2 = mydf.squeeze(axis=0)

#def test_calc_ReqMem():
#    with open( SINGLE_USER_SACCT_FILE, 'rb') as f: # Move this to a setup func
#        logs_raw = f.read()  # A Pandas dataframe
#
#    logs_df = pd.read_csv(BytesIO(logs_raw), sep="|", dtype='str')
#    jobid = "7611224"
#    mydf = logs_df[logs_df.JobID == jobid]
#    if len(mydf) > 1:
#        # raise pytest error message here
#        return
#    myseries = mydf.squeeze(axis=0)
#
#    HWM = Helpers_WM(None)
#    mem_gb = HWM.calc_ReqMem(myseries)
#    assert mem_gb == 300.75

# x['ReqMem'], x['NNodes'], x['NCPUS']
    
@pytest.mark.parametrize("reqmem, nnodes, ncpus, expected",  
    [   
        ("60150M", 1, 5, 60.15),
        ("201Mn", 3, 1, 0.603),
        ("0.0001Gc", 1, 3, 0.0003)
    ],) 
def test_calc_ReqMem(reqmem, nnodes, ncpus, expected):
    HWM = Helpers_WM(None)
    dictionary = {'ReqMem': reqmem, 'NNodes': nnodes, 'NCPUS': ncpus}
    myseries = pd.Series(dictionary)
    try:
        assert HWM.calc_ReqMem(myseries) == expected
    except AssertionError:
        assert HWM.calc_ReqMem(myseries) == pytest.approx(expected)
    

# We might not need to test all of these. They are here simply as an aide memoire for now.
def test_clean_RSS():
    pass

def test_clean_UsedMem():
    pass

def test_clean_partition():
    pass

def test_set_partitionType():
    pass

# etc ...
