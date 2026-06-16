# ------------------------------------------------------------------
# Utitlity/helper functions
# ------------------------------------------------------------------

import datetime
from io import BytesIO
import os
import sys
import pandas as pd

def concat_dataframes(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """
    Concatenate DataFrames after filtering out empty or all-NaN inputs.

    This ensures consistent dtype inference and avoids future incompatibilities with pandas, 
    where concatenation behavior with empty or all-NaN DataFrames is changing (FutureWarning).
    """

    # Keep only DataFrames that are not empty and not entirely NaN
    dfs = [df for df in dfs if not df.empty and not df.isna().all().all()]
    
    return pd.concat(dfs, ignore_index=True)

def convert2dataframe(df_raw: bytes, types: dict | None = None, delimiter="|"):
    """
    Convert raw logs output into a pandas DataFrame.
    Parameters:
        df_raw : Raw logs output as bytes.
        types : column names and their desired data types. E.g., {'NNodes': 'int64', 'NCPUS': 'int64'}
        delimiter : Delimiter used in the raw logs.
    Returns:
        pd.DataFrame: DataFrame containing the parsed logs with specified data types.
    """
    df = pd.read_csv(BytesIO(df_raw), sep=delimiter, dtype='str')

    # Convert specified columns to appropriate data types 
    if types:
        for c, t in types.items():
            if c in df.columns:
                df[c] = df[c].astype(t)
    return df

def check_empty_results(df, args):
    """
    This is to check whether any jobs have been run in the period, and stop the script if not.
    :param df: [pd.DataFrame] Usage logs
    :param args: [argStruct] Named tuple of arguments used.
    """
    if len(df) == 0:
        if args.filterWD is not None:
            addThat = f' from this directory ({args.filterWD})'
        else:
            addThat = ''
        if args.filterJobIDs != 'all':
            addThat += ' and with these jobIDs'
        if args.filterAccount is not None:
            addThat += ' charged under this account'

        print(f'''

    You haven't run any jobs in that period (from {args.startDay} to {args.endDay}){addThat}.

        ''')
        sys.exit()

##DEBUGONLY 
def get_mock_agg_data() -> pd.DataFrame:
    """
    Read and return mock aggregated data from a pickled file. Mock data generated using 'simulate_mock_jobs()' function.
    """
    # Steps done in pickle_it.py script:
    # df2 = simulate_mock_jobs()
    # df2.to_pickle("testdata/df_agg_X_mockMultiUsers_1.pkl")
    # NB the data generated is different each time.

    # foo = 'testdata/df_agg_test_3.pkl'
    # foo = 'testdata/df_agg_X_1.pkl'

    has_slurmAdmin = True # Assuming we have admin access
    if has_slurmAdmin: 
        pickled_test_data = 'tests/testdata/df_agg_X_mockMultiUsers_2.pkl'
        
    print(f"Overriding df_agg with `{pickled_test_data}`")
    return pd.read_pickle(pickled_test_data)

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