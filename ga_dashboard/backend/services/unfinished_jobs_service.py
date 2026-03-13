import pandas as pd
import datetime

from ga_dashboard.backend.helpers import utils
from ga_dashboard.backend.services.database_service import DBSettings, DatabaseService
from ga_dashboard.backend.services.sacct_service import SacctService
from ga_dashboard.database.table_col_definitions import UNFINISHED_JOBS_COLUMNS

## States from SLURM documentation: https://slurm.schedmd.com/job_state_codes.html (as of 10 Feb 2026)

SLURM_STATES = ['BOOT_FAIL','CANCELLED','COMPLETED','DEADLINE','FAILED','NODE_FAIL','OUT_OF_MEMORY','PENDING','PREEMPTED','RUNNING','SUSPENDED','TIMEOUT','UNKNOWN']
FINISHED_STATES = ['BOOT_FAIL','CANCELLED','COMPLETED','DEADLINE','FAILED','NODE_FAIL','OUT_OF_MEMORY','TIMEOUT']
UNFINISHED_STATES = ['PENDING','RUNNING','SUSPENDED','UNKNOWN','PREEMPTED']

class UnfinishedJobsService:
    def __init__(self, config_data: dict, db_params: DBSettings):
        self.config_data = config_data
        self.db_params = db_params

    def filter_unfinished_jobs(self, logs_df: pd.DataFrame) -> pd.DataFrame:
        '''
        
        Filter unfinished jobs from the logs dataframe using the 'State' column (if 'End' column is not available) or the 'End' column (if available).
        '''
        if 'End' in logs_df.columns:
            mask = logs_df['End'].isna() | (logs_df['End'] == 'Unknown')
        else:
            mask = logs_df['State'].isin(UNFINISHED_STATES)
        
        return logs_df[mask].copy(), logs_df[~mask].copy() # Return both unfinished and finished jobs for further processing
    
    def filter_finished_jobs(self, logs_df: pd.DataFrame) -> pd.DataFrame:
        '''
        Filter finished jobs from the logs dataframe using the 'State' column (if 'End' column is not available) or the 'End' column (if available).
        '''
        if 'End' in logs_df.columns:
            mask = logs_df['End'].notna() & (logs_df['End'] != "Unknown")
        else:
            mask = logs_df['State'].isin(FINISHED_STATES)
        
        return logs_df[mask].copy()
    
    def sync_unfinished_jobs(self) -> pd.DataFrame:
        '''
        Get the list of unfinished jobs from the previous extraction (if any) to check if they are still unfinished or if they have finished in the meantime.
        Pull the jobs using sacct command on the basis of Job IDs
        '''
        use_mock = True if 'use_mock' in self.config_data.keys() and self.config_data['use_mock'] else False
        if use_mock:
            prev_unfinished_jobs_df = pd.read_csv(self.config_data['use_mock'])
        else:
            with DatabaseService(self.db_params) as database:
                prev_unfinished_jobs_df = database.fetch_data(
                    table_name='ga_unfinished_jobs',
                    columns=UNFINISHED_JOBS_COLUMNS
                )
        
        #Fetching unfinished job using sacct command
        raw_logs = SacctService.pull_logs_by_jobid(prev_unfinished_jobs_df) 
        if raw_logs is not None:
            raw_logs_df = utils.convert2dataframe(raw_logs, types = {'NNodes': 'int64', 'NCPUS': 'int64'})
            finished_jobs = self.filter_finished_jobs(raw_logs_df)
            #creating a list to track the finished jobs ids
            self.finished_jobids = finished_jobs['JobID'].apply(lambda x: x.split('.')[0]).unique().tolist()
            return finished_jobs
        return None

    def save_unfinished_jobs(self, unfinished_jobs_df: pd.DataFrame):
        '''
        Save the unfinished jobs to the 'unfinished_jobs' table in the database.
        '''
        unfinished_jobs_df = unfinished_jobs_df.rename(columns={
            'User':   'user_name',
            'JobID':  'job_id',
            'Submit': 'submitdate',
            'Start':  'startdate',
            'State':  'job_state',
        })

        unfinished_jobs_df['submitdate'] = pd.to_datetime(
            unfinished_jobs_df['submitdate'],
            format="%Y-%m-%dT%H:%M:%S",
            errors="coerce"   # invalid parses -> NaT
        )
        
        unfinished_jobs_df['startdate'] = pd.to_datetime(
            unfinished_jobs_df['startdate'],
            format="%Y-%m-%dT%H:%M:%S",
            errors="coerce"   # invalid parses -> NaT
        )

        with DatabaseService(self.db_params) as database:
            database.insert_data(
                table_name='ga_unfinished_jobs',
                rows = unfinished_jobs_df.to_dict(orient='records'),
                columns=UNFINISHED_JOBS_COLUMNS,
            )

    def delete_resolved_unfinished_jobs(self):
        '''
        Delete the jobs that were previously unfinished but have now finished from the 'unfinished_jobs' table in the database.
        '''
        if hasattr(self, 'finished_jobids') and self.finished_jobids:
            with DatabaseService(self.db_params) as database:
                database.delete_by_column_values(
                    table_name='ga_unfinished_jobs',
                    column_name='job_id',
                    values=self.finished_jobids)
        else:
            print("No finished jobs to delete from unfinished_jobs table.")
            