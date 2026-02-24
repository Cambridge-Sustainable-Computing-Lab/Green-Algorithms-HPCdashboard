import pandas as pd

from ga_dashboard.backend.helpers import utils
from ga_dashboard.backend.services.database_service import DBSettings, DatabaseService
from ga_dashboard.backend.services.sacct_service import SacctService
from ga_dashboard.database.table_col_definitions import UNFINISHED_JOBS_COLUMNS

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
    
    def handle_running_jobs(self, logs_df: pd.DataFrame) -> pd.DataFrame:
        ##Add running jobs to the database
        return None


    
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
            db_params = DBSettings(
                db_name=self.config_data['db_name'],
                user=self.config_data['db_user'],
                password=self.config_data['db_password'],
                host=self.config_data['db_host'],
                port=self.config_data['db_port']
                )

            with DatabaseService(db_params) as database:
                prev_unfinished_jobs_df = database.fetch_data(
                    table_name='unfinished_jobs',
                    columns=UNFINISHED_JOBS_COLUMNS
                )
        
        #Fetching unfinished job using sacct command
        raw_logs = SacctService.pull_logs_by_jobid(prev_unfinished_jobs_df) 
        raw_logs_df = utils.convert2dataframe(raw_logs, types = {'NNodes': 'int64', 'NCPUS': 'int64'})
        finished_jobs = self.filter_finished_jobs(raw_logs_df)

        return finished_jobs
    
    def delete_resolved_unfinished_jobs(self, finished_jobs_df: pd.DataFrame):
        '''
        Delete the jobs that were previously unfinished but have now finished from the 'unfinished_jobs' table in the database.
        '''
        db_params = DBSettings(
            db_name=self.config_data['db_name'],
            user=self.config_data['db_user'],
            password=self.config_data['db_password'],
            host=self.config_data['db_host'],
            port=self.config_data['db_port']
            )
        job_ids = finished_jobs_df['JobID'].tolist()

        with DatabaseService(db_params) as database:
            database.delete_by_column_values(
                table_name='unfinished_jobs',
                column_name='job_id',
                values=job_ids)
            