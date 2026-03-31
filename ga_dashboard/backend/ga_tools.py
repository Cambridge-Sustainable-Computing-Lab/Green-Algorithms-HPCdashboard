# ------------------------------------------------------------------
# Main tools to extract, enrich and summarise data for the GA4HPC dashboard.
# ------------------------------------------------------------------

import numpy as np
import pandas as pd
import yaml
import time as time_module
import gc
from tqdm import tqdm
from datetime import datetime, time, timedelta

from ga_dashboard.backend.services.carbon_intensity_service import CarbonIntensityService, JobEmissionRecord
import ga_dashboard.backend.helpers.utils as utils
from ga_dashboard.backend.workload_manager.slurm import SlurmManager
from ga_dashboard.backend.data_sql_import import DataSQLImport
from ga_dashboard.backend.services.database_service import DBSettings
from ga_dashboard.backend.services.unfinished_jobs_service import UnfinishedJobsService


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


class GA_tools:

    def __init__(self, cluster_info, fixed_params):
        self.cluster_info = cluster_info
        self.fixed_params = fixed_params

    def calculate_energies(self, row):
        '''
        Calculate the energy usage based on the job's parameters
        :param row: [pd.Series] one row of usage statistics, corresponding to one job
        :return: [pd.Series] the same statistics with the energies added
        '''
        ### CPU and GPU
        partition_info = None

        try:
            partition_info = self.cluster_info['partitions'][row.PartitionX]
        except KeyError as ke:
            # Raise error if key not found.
            # TODO Make checking of all keys more robust, and explain what to do when a key is missing.
            print(f"calculate_energies(): KeyError: {ke}. Exiting...")
            exit

        if not partition_info:  #is None:
            print("calculate_energies(): partition_info is None. Exiting...")
            exit

        if row.PartitionTypeX == 'CPU':
            TDP2use4CPU = partition_info['TDP']
            TDP2use4GPU = 0
        else:
            TDP2use4CPU = partition_info['TDP_CPU']
            TDP2use4GPU = partition_info['TDP']

        row['energy_CPUs'] = row.TotalCPUtime2useX.total_seconds() / 3600 * TDP2use4CPU / 1000  # in kWh

        row['energy_GPUs'] = row.TotalGPUtime2useX.total_seconds() / 3600 * TDP2use4GPU / 1000  # in kWh

        ### memory
        for suffix, memory2use in zip(['','_memoryNeededOnly'], [row.ReqMemX,row.NeededMemX]):
            row[f'energy_memory{suffix}'] = row.WallclockTimeX.total_seconds()/3600 * memory2use * self.fixed_params['power_memory_perGB'] /1000 # in kWh
            row[f'energy{suffix}'] = (row.energy_CPUs +  row.energy_GPUs + row[f'energy_memory{suffix}']) * self.cluster_info['PUE'] # in kWh

        return row

    def calculate_carbonFootprint_default(self, df, col_energy):
        return df[col_energy] * self.cluster_info['CI']
    
    def calculate_carbonFootprint(self, row: pd.Series, suffix: str, daily_avg_CI: dict) -> pd.DataFrame:
        """
        Expand a job record (1 row) into per day records with energy usage on that day, hours of work on that day, and daily avg CI.
        Calculate the total carbon emissions for the job.
        :param row: a row from the job dataframe
        :param suffix: suffix for energy column (e.g. '', '_memoryNeededOnly', '_failedJobs')
        :param daily_avg_CI: dictionary mapping dates to their average carbon intensity values
        """

        start = row['StartDatetimeX']
        end = row['EndDatetimeX']
        energy = row[f'energy{suffix}']
        tot_duration_hours = row['WallclockTimeX'].total_seconds() / 3600
        # Assuming energy is consumed uniformly across the job duration
        energy_per_hr = energy / tot_duration_hours if tot_duration_hours > 0 else 0 # Avoid division by zero

        day_job_emissions = []
        current_day = start

        # Per day energy use, hours of work, and CI
        while current_day.date() <= end.date():
            day_start = max(current_day, datetime.combine(current_day.date(), time.min))
            day_end = min(end, datetime.combine(current_day.date(), time.max))
            hours = (day_end - day_start).total_seconds() / 3600
            day_avg_CI = daily_avg_CI.get(current_day.strftime('%d-%m-%Y'), None)

            day_job_emissions.append(JobEmissionRecord(current_day, energy_per_hr, hours, day_avg_CI))
            
            # Advance to midnight of next day
            current_day = datetime.combine(current_day.date() + timedelta(days=1), time.min)

        return JobEmissionRecord.calc_carbon_emission(day_job_emissions, energy_per_hr)

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

        # GA_tools object
        self.GA = GA_tools(self.cluster_info, self.fixed_params)

        self.has_slurmAdmin = True
        self.config_data = config_data

    def extract_data(self):
        if 'use_mock_agg_data' in self.config_data.keys(): # DEBUGONLY Create/use some mock jobs with different users
            return utils.get_mock_agg_data(), UnfinishedJobsService(self.config_data, self.db_params) # Returining empty UnfinishedJobsService to avoid errors later, but it's not used.
        
        ### Pull usage statistics from the workload manager
        WM = SlurmManager(self.config_data, self.cluster_info)
        WM.pull_logs()

        ### Log the output for debugging
        utils.save_slurm_logs(self.config_data, WM)

        unfinished_jobs_service = UnfinishedJobsService(self.config_data, self.db_params)

        ### Turn usage logs into DataFrame
        WM.raw_logs_to_df()

        # get unfinished jobs from db and pick those that have now finished using sacct command by job id
        finished_jobs_df = unfinished_jobs_service.sync_unfinished_jobs() 
    
        WM.filter_and_store_unfinished_jobs(unfinished_jobs_service) # Filter unifinshed jobs from WM logs and store them in DB

        if finished_jobs_df is not None:
            WM.concat_logs_df(finished_jobs_df) #concat finished jobs (previously unfinished) with rest of the logs

        # And clean
        WM.clean_logs_df()
        # Check if there are any jobs during the period from this directory and with these jobIDs
        utils.check_empty_results(WM.df_agg, self.config_data)

        # Check that there is only one user's data if no admin right
        if not self.has_slurmAdmin:
            if len(set(WM.df_agg_X.UserX)) > 1:
                raise ValueError(f"More than one user's logs was included, despite --slurmAdmin not used: {set(WM.df_agg_X.UserX)}")

        # WM.df_agg_X.to_pickle("testdata/df_agg_X_1.pkl") # DEBUGONLY used to test different steps offline

        return WM.df_agg_X, unfinished_jobs_service
    
    def enrich_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Adds data about the carbon footprint, etc.
        :param df: [pd.DataFrame] The existing data we've extracted.
        :param fixed_params: [dict] The fixed parameters used.
        :param GA [GA_tools] A GA_tools object. 
        :return: [pd.DataFrame] The enriched data.
        """
        
        ### energy
        df = df.apply(self.GA.calculate_energies, axis=1)

        try:
            df['energy_failedJobs'] = np.where(df.StateX == 0, df.energy, 0)
        except AttributeError as err:
            print(f"enrich_data(): AttributeError: {err}")
            # TODO Explain this error, and what to do about it.
            return None  # or should we exit?
        
        ### Fetching Carbon Intensity
        postcode = self.cluster_info.get('postcode', None)
        ci_avg_data = {}
        if postcode:
            postcode = postcode[:3] # Taking only the first three letters from the postcode
            ci_service = CarbonIntensityService(postcode, self.db_params)
            ci_avg_data = ci_service.calc_day_average_CI(df.StartDatetimeX.min(), df.EndDatetimeX.max())

        ### carbon footprint
        for suffix in ['', '_memoryNeededOnly', '_failedJobs']:
            if ci_avg_data:
                df[f'carbonFootprint{suffix}'] = df.apply(
                    lambda row: self.GA.calculate_carbonFootprint(row, suffix, ci_avg_data),
                    axis=1
                )
            else: #use default CI value from cluster yaml
                df[f'carbonFootprint{suffix}'] = self.GA.calculate_carbonFootprint_default(df, f'energy{suffix}')

            # Context metrics (part 1)
            df[f'treeMonths{suffix}'] = df[f'carbonFootprint{suffix}'] / self.fixed_params['tree_month']
            df[f'cost{suffix}'] = df[f'energy{suffix}'] * self.fixed_params['electricity_cost']

        ### Context metrics (part 2)
        df['driving'] = df.carbonFootprint / self.fixed_params['passengerCar_EU_perkm']
        df['flying_NY_SF'] = df.carbonFootprint / self.fixed_params['flight_NY_SF']
        df['flying_PAR_LON'] = df.carbonFootprint / self.fixed_params['flight_PAR_LON']
        df['flying_NYC_MEL'] = df.carbonFootprint / self.fixed_params['flight_NYC_MEL']

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

        return df2
    
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

        df['SubmitDate'] = df.SubmitDatetimeX.dt.date  # TODO do it with real start time rather than submit date
        has_slurmAdmin = True # get_slurmAdmin(args) # We only assume we have admin access now

        if has_slurmAdmin:
            # With daily figures
            df_userdaily = agg_jobs(df, ['User', 'UID', 'Name', 'Group', 'Department', 'SubmitDate'])
            output = {'userDaily': df_userdaily}

        # Some job-level statistics to plot distributions
        memoryOverallocationFactors = df.groupby('UserX')['memOverallocationFactorX'].apply(list).to_dict()
        memoryOverallocationFactors['overall'] = df.memOverallocationFactorX.to_numpy()
        output['memoryOverallocationFactors'] = memoryOverallocationFactors

        return output
    
    def process_and_store(self, summary_stats:dict, unfinished_jobs_service:UnfinishedJobsService) -> None:
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
        
        #only delete the finished jobs from ga_unfinished_jobs table after the new data has been successfully inserted
        unfinished_jobs_service.delete_resolved_unfinished_jobs()

    def run(self) -> pd.DataFrame:
        """
        Pipeline run that extracts logs, processes the data, summarises it, and stores in Database

        :return: pandas Dataframe containing processed data
        """
        df, unfinished_jobs_service = self.extract_data()
        df2 = self.enrich_data(df)

        del df # df is potentially large and no longer needed 

        summary_stats = self.summarise_data(df2)

        del df2 # df2 is potentially large and no longer needed 
        gc.collect()

        self.process_and_store(summary_stats, unfinished_jobs_service)

        return summary_stats
    
    def batch_run(self, batch_size: int = 30) -> dict:
        """
        Create batches of dates (default = 30 days per batch) between startDay and endDay.
        Run processing pipeline for each batch.
        :param batch_size: size of batch in number of days
        :return: dict containing summary stats for all batches
        """
        if 'useCustomLogs' in self.config_data.keys() and self.config_data['useCustomLogs'] != '':
                print("useCustomLogs found in config. Skipping batch processing.")
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