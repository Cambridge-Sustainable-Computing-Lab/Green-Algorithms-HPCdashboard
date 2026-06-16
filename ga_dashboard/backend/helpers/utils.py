# ------------------------------------------------------------------
# utility and DEBUGONLY functions (add new generic utlity functions here)
# ------------------------------------------------------------------

import datetime
import os
import sys
import random
import pandas as pd
import numpy as np
from datetime import timedelta
from io import BytesIO

def parse_string_to_number(s:str) -> int | float | str:
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s
        
def generate_batches_by_dates(start: str | datetime.date, end: str | datetime.date, batch_size: int = 30) -> list:
    """
    Generates date ranges (start and end pairs) that divide a larger time period into batches.

    Parameters:
        start : date to start batching from
        end : date when batching ends
        batch_size : number of days in a batch
    
    Returns:
        List of tuples where each tuple is a pair of two dates.
    """
    if isinstance(start, str):
        start = datetime.datetime.strptime(start, "%Y-%m-%d").date()
    if isinstance(end, str):
        end = datetime.datetime.strptime(end, "%Y-%m-%d").date()

    batches = []
    current_start = start

    while current_start <= end:
        current_end = min(current_start + timedelta(days=batch_size - 1), end)
        start_ts = f"{current_start}T00:00:00"
        end_ts = f"{current_end}T23:59:59"
        batches.append((start_ts, end_ts))
        current_start = current_end + timedelta(days=1)

    return batches

##DEBUGONLY 
def simulate_mock_jobs():
    df_list = []
    for user in ['uid_1', 'uid_2', 'uid_3', 'uid_4', 'uid_5']:
        n_jobs = random.randint(500,800)
        data_dict = {
            'WallclockTimeX':[datetime.timedelta(minutes=random.randint(50,700)) for _ in range(n_jobs)],
            'ReqMemX':np.random.randint(4,130, size=n_jobs)*1.,
            'PartitionX':['yew']*n_jobs,
            'SubmitDatetimeX':[datetime.datetime(day=1,month=5,year=2023) + datetime.timedelta(days=random.randint(1,60)) for _ in range(n_jobs)],
            'StateX':np.random.choice([1,0], p=[.8,.2], size=n_jobs),
            'UIDX':['11111']*n_jobs,
            'UserX':[user]*n_jobs,
            'PartitionTypeX':['CPU']*n_jobs,
            'TotalCPUtime2useX':[datetime.timedelta(minutes=random.randint(50,5000)) for _ in range(n_jobs)],
            'TotalGPUtime2useX':[datetime.timedelta(seconds=0)]*n_jobs,
        }

        data_frame = pd.DataFrame(data_dict)
        data_frame['CPUhoursChargedX'] = data_frame.TotalCPUtime2useX / np.timedelta64(1, 'h')
        data_frame['GPUhoursChargedX'] = 0.
        data_frame['NeededMemX'] = data_frame.ReqMemX * np.random.random(n_jobs)
        data_frame['memOverallocationFactorX'] = data_frame.ReqMemX / data_frame.NeededMemX

        df_list.append(data_frame)

    return pd.concat(df_list)

##DEBUGONLY 
def save_slurm_logs(config_data, WM) -> None:
    """
    Save raw SLURM logs to a CSV file for later inspection.
    legacy from GA4HPC - gives an option to export the logs to test the code on them in cases where we cannot see others' logs.

    Parameters:
        config_data (dict): Configuration dictionary that may contain keys like 'saveSlurmLogs' or 'saveSlurmLogsHere'.
            If 'saveSlurmLogs' exists, logs are saved in a default error_logs directory.
            If 'saveSlurmLogsHere' exists, logs are saved in the user's current working directory.
        WM (SlurmManager): Instance of SlurmManager containing SLURM logs in `logs_raw`.
    """
    if 'saveSlurmLogs' in config_data or 'saveSlurmLogsHere' in config_data:
        # Generate unique filename using timestamp
        log_name = str(datetime.datetime.now().timestamp()).replace(".", "_")

        scripts_dir = os.path.dirname(os.path.realpath(__file__))

        if 'saveSlurmLogs' in config_data:
            log_path = os.path.join(scripts_dir, '../error_logs', f'sacctOutput_{log_name}.csv')
        else: # i.e. config_data['saveSlurmLogsHere'] is True
            log_path = os.path.join(config_data["userCWD"], f'sacctOutput_{log_name}.csv')

        # Ensure the directory exists
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        # Save raw SLURM logs to file
        with open(log_path, 'wb') as f:
            f.write(WM.logs_raw)

        print(f"\nSLURM statistics saved for inspection: {log_path}\n")

##DEBUGONLY 
def quick_inspect(df: pd.DataFrame, name: str = "DataFrame") -> None:
    """
    Utility function to quickly inspect a DataFrame by printing its shape, columns, datatypes, and head.
    """
    print(f"--- Quick Inspection of {name} ---")
    print("Shape:", df.shape)
    print("Columns:", df.columns.tolist())
    print("Dtypes:\n", df.dtypes)
    print("Head:\n", df.head())
    print(f"--- End of {name} Inspection ---\n")



