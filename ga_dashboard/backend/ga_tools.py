# ------------------------------------------------------------------
# Main tools to extract, enrich and summarise data for the GA4HPC dashboard.
# ------------------------------------------------------------------

import pandas as pd
import yaml
import time as time_module
import gc
from tqdm import tqdm
import ga_core

from ga_dashboard.backend.services.database_ci_store import DatabaseCIStore
import ga_dashboard.backend.helpers.utils as utils
from ga_dashboard.backend.data_sql_import import DataSQLImport
from ga_dashboard.backend.services.database_service import DBSettings


agg_functions_from_raw = {
        'n_jobs': ('UserX', 'count'),
        'first_job_period': ('SubmitDatetimeX', 'min'),
        'last_job_period': ('SubmitDatetimeX', 'max'),
        'energy': ('energy', 'sum'),
        'energy_CPUs': ('energy_CPUs', 'sum'),
        'energy_GPUs': ('energy_GPUs', 'sum'),
        'energy_memory': ('energy_memory', 'sum'),
        'carbonFootprint': ('carbonFootprint', 'sum'),
        'carbonFootprint_memoryNeededOnly': ('carbonFootprint_memoryNeededOnly', 'sum'),
        'carbonFootprint_failedJobs': ('carbonFootprint_failedJobs', 'sum'),
        'cpuTime': ('TotalCPUtime2useX', 'sum'),
        'gpuTime': ('TotalGPUtime2useX', 'sum'),
        'wallclockTime': ('WallclockTimeX', 'sum'),
        'CPUhoursCharged': ('CPUhoursChargedX', 'sum'),
        'GPUhoursCharged': ('GPUhoursChargedX', 'sum'),
        'memoryRequested': ('ReqMemX', 'sum'),
        'memoryOverallocationFactor': ('memOverallocationFactorX', 'mean'),
        'n_success': ('StateX', 'sum'),
        'treeMonths': ('treeMonths', 'sum'),
        'treeMonths_memoryNeededOnly': ('treeMonths_memoryNeededOnly', 'sum'),
        'treeMonths_failedJobs': ('treeMonths_failedJobs', 'sum'),
        'driving': ('driving', 'sum'),
        'flying_NY_SF': ('flying_NY_SF', 'sum'),
        'flying_PAR_LON': ('flying_PAR_LON', 'sum'),
        'flying_NYC_MEL': ('flying_NYC_MEL', 'sum'),
        'cost': ('cost', 'sum'),
        'cost_failedJobs': ('cost_failedJobs', 'sum'),
        'cost_memoryNeededOnly': ('cost_memoryNeededOnly', 'sum'),
    }

class LogsDataProcessor:
    """
    Data processor class to load settings, extract, process, and store logs.
    """
    def __init__(self, config_data: dict):
        """
        Loads cluster information, fixed parameters file, database settings, and users information using config data.
        Initialses Green Algorithms Tools (GA_tools) object - used for processing logs.

        :param config_data: dict containing configurations from config file
        """
        # Load cluster info
        with open(config_data['cluster_info_file'], 'r') as f:
            self.cluster_info = yaml.safe_load(f)

        # Load fixed params
        with open(config_data['fixed_params_file'], 'r') as f:
            self.fixed_params = yaml.safe_load(f)

        # DB settings
        self.db_params = DBSettings(
            db_name=config_data['db_name'],
            user=config_data['db_user'],
            password=config_data['db_password'],
            host=config_data['db_host'],
            port=config_data['db_port']
        )

        # Load users if available
        try:
            self.users_df = pd.read_csv(config_data['dashboard_users_file'])
        except FileNotFoundError:
            self.users_df = None


        self.has_slurmAdmin = True
        self.config_data = config_data
    
    def summarise_data(self, df: pd.DataFrame) -> dict:

        if df is None:
            print("summarise_data(): df is None")
            return None

        # This is to aggregate already aggregated dataset (so names are a bit different)
        agg_functions_further = agg_functions_from_raw.copy()
        data2aggregate = {
            'n_jobs':'sum',
            'first_job_period':'min',
            'last_job_period': 'max',
            'cpuTime': 'sum',
            'gpuTime': 'sum',
            'wallclockTime': 'sum',
            'CPUhoursCharged': 'sum',
            'GPUhoursCharged': 'sum',
            'memoryRequested': 'sum',
            'memoryOverallocationFactor': 'mean', # NB: not strictly correct to do a mean of mean, but ok
            'n_success': 'sum'
        }
        for agg_col, agg_method in data2aggregate.items():
            agg_functions_further[agg_col] = (agg_col, agg_method)

        def agg_jobs(data, agg_names=None):
            """

            :param data:
            :param agg_names: if None, then the whole dataset is aggregated
            :return:
            """
            agg_names2 = agg_names if agg_names else lambda _:True
            if 'UserX' in data.columns:
                timeseries = data.groupby(agg_names2).agg(**agg_functions_from_raw)
            else:
                timeseries = data.groupby(agg_names2).agg(**agg_functions_further)
    
            timeseries.reset_index(inplace=True, drop=(agg_names is None))
            timeseries['success_rate'] = timeseries.n_success / timeseries.n_jobs
            timeseries['failure_rate'] = 1 - timeseries.success_rate
            timeseries['share_carbonFootprint'] = timeseries.carbonFootprint / timeseries.carbonFootprint.sum()

            return timeseries

        df['SubmitDate'] = df.SubmitDatetimeX.dt.date
        has_slurmAdmin = True # get_slurmAdmin(args) # Assuming we have admin access

        if has_slurmAdmin:
            # With daily figures
            df_userdaily = agg_jobs(df, ['User', 'UID', 'Name', 'Group', 'Department', 'SubmitDate'])
            output = {'userDaily': df_userdaily}

        # Some job-level statistics to plot distributions
        memoryOverallocationFactors = df.groupby('UserX')['memOverallocationFactorX'].apply(list).to_dict()
        memoryOverallocationFactors['overall'] = df.memOverallocationFactorX.to_numpy()
        output['memoryOverallocationFactors'] = memoryOverallocationFactors

        return output
    
    def process_and_store(self, summary_stats:dict) -> None:
        # Import aggregated data into a database
        data2db = DataSQLImport(
                    summary_stats,
                    self.db_params
                )
        try: 
            data2db.insert_data_into_db()
        except Exception as e:
            print(f"Error occurred while inserting data into database: {e}")
            return
        

    def run(self) -> pd.DataFrame:
        """
        Pipeline run that extracts logs, processes the data, summarises it, and stores in Database

        :return: pandas Dataframe containing processed data
        """
        dataprocessor = ga_core.HPCDataProcessor(self.config_data, self.cluster_info, self.fixed_params, self.has_slurmAdmin)
        df = dataprocessor.extract_data()
        db_ci_store = DatabaseCIStore(self.db_params)
        df = dataprocessor.enrich_data(df, db_ci_store)

        ### Add user details to jobs
        if self.users_df is None:
            print("No user info to add.")
            df2 = df
        else:
            df2 = pd.merge(df, self.users_df, left_on='UserX', right_on='User', how='inner')
            if len(df2) != len(df):
                # This basically raises an error if a user in the df isn't in the users_df,
                # which is obtained from the file listing the HPC users.
                raise ValueError("Not all users could be matched!")

        del df # df is potentially large and no longer needed 

        summary_stats = self.summarise_data(df2)

        del df2 # df2 is potentially large and no longer needed 
        gc.collect()

        self.process_and_store(summary_stats)

        return summary_stats
    
    def batch_run(self, batch_size: int = 30) -> dict:
        """
        Create batches of dates between startDay and endDay.
        Run processing pipeline for each batch.
        :param batch_size: size of batch in number of days
        :return: dict containing summary stats for all batches
        """
        if self.config_data.get('useCustomLogs', '') != '' or self.config_data.get('use_mock_agg_data', '') != '':
                return self.run()
        
        batches = utils.generate_batches_by_dates(
            start=self.config_data["startDay"],
            end=self.config_data["endDay"],
            batch_size=batch_size,
        )
        n = len(batches)
        failed = []
        t_run = time_module.perf_counter()

        print(f"\nBatch size: {batch_size} days")
        print(f"Number of batches: {n} \n")

        batch_iter = tqdm(batches, desc="Processing batches", unit="batch")
        summary_stats_all = {}

        for i, dates_pair in enumerate(batch_iter, 1):
            start_date, end_date = dates_pair[0], dates_pair[1]
            t_batch = time_module.perf_counter()

            batch_iter.set_postfix(current=f"{start_date} to {end_date}")

            try:
                self.config_data['startDay'] = start_date
                self.config_data['endDay']   = end_date
                summary_stats = self.run() # Run data processing pipeline
                summary_stats_all |= summary_stats

                del summary_stats # summary_stats contains multiple dfs, potentially large and no longer needed
                gc.collect()

                elapsed = time_module.perf_counter() - t_batch
                tqdm.write(f"  [{i}/{n}] {start_date} to {end_date}  {elapsed:.1f}s")

            except Exception as e:
                tqdm.write(f"  [{i}/{n}] {start_date} to {end_date}  failed: {e}")
                failed.append((start_date, end_date))

        elapsed_total = time_module.perf_counter() - t_run
        status = f"({len(failed)} failed)" if failed else "(0 failed)"
        print(f"\n{n - len(failed)} of {n} batches completed in {elapsed_total:.1f}s  {status}")
        if failed:
            for f in failed:
                print(f"  {f[0]} to {f[1]}")

        return summary_stats_all