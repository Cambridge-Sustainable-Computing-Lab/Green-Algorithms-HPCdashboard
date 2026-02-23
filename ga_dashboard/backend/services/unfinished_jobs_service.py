import pandas as pd

## States from SLURM documentation: https://slurm.schedmd.com/job_state_codes.html (as of 10 Feb 2026)

SLURM_STATES = ['BOOT_FAIL','CANCELLED','COMPLETED','DEADLINE','FAILED','NODE_FAIL','OUT_OF_MEMORY','PENDING','PREEMPTED','RUNNING','SUSPENDED','TIMEOUT','UNKNOWN']
FINISHED_STATES = ['BOOT_FAIL','CANCELLED','COMPLETED','DEADLINE','FAILED','NODE_FAIL','OUT_OF_MEMORY','TIMEOUT']
UNFINISHED_STATES = ['PENDING','RUNNING','SUSPENDED','UNKNOWN','PREEMPTED']

class UnfinishedJobsService:
    def __init__(self, config_data):
        self.config_data = config_data

    def filter_unfinished_jobs(self, logs_df: pd.DataFrame) -> pd.DataFrame:
        '''
        
        Filter unfinished jobs from the logs dataframe using the 'State' column (if 'End' column is not available) or the 'End' column (if available).
        '''
        if 'End' in logs_df.columns:
            mask = logs_df['End'].isna()
        else:
            mask = logs_df['State'].isin(UNFINISHED_STATES)
        
        return logs_df[mask].copy()
    
    def filter_finished_jobs(self, logs_df: pd.DataFrame) -> pd.DataFrame:
        '''
        Filter finished jobs from the logs dataframe using the 'State' column (if 'End' column is not available) or the 'End' column (if available).
        '''
        if 'End' in logs_df.columns:
            mask = logs_df['End'].notna()
        else:
            mask = logs_df['State'].isin(FINISHED_STATES)
        
        return logs_df[mask].copy()