# ------------------------------------------------------------------
# Main tools to extract, enrich and summarise data for the GA4HPC dashboard.
# ------------------------------------------------------------------

import numpy as np
import pandas as pd
import yaml
from datetime import datetime, time

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
            current_day += pd.Timedelta(days=1)

        return JobEmissionRecord.calc_carbon_emission(day_job_emissions, energy_per_hr)


def extract_data(config_data: dict, has_slurmAdmin: bool, cluster_info, db_params: DBSettings) -> pd.DataFrame:

    if 'use_mock_agg_data' in config_data.keys(): # DEBUGONLY Create/use some mock jobs with different users

        # Steps done in pickle_it.py script:
        # df2 = simulate_mock_jobs()
        # df2.to_pickle("testdata/df_agg_X_mockMultiUsers_1.pkl")
        # NB the data generated is different each time.

        # foo = 'testdata/df_agg_test_3.pkl'
        # foo = 'testdata/df_agg_X_1.pkl'
        
        if has_slurmAdmin: # TODO remove `has_slurmAdmin` as it's not needed in the dashboard anymore
            pickled_test_data = 'tests/testdata/df_agg_X_mockMultiUsers_1.pkl'
        else:
            pickled_test_data = 'tests/testdata/df_agg_X_1.pkl'
        print(f"Overriding df_agg with `{pickled_test_data}`")
        return pd.read_pickle(pickled_test_data), UnfinishedJobsService(config_data)


    ### Pull usage statistics from the workload manager
    WM = SlurmManager(config_data, cluster_info)
    WM.pull_logs()

    ### Log the output for debugging
    utils.save_slurm_logs(config_data, WM)

    unfinished_jobs_service = UnfinishedJobsService(config_data, db_params)

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
    utils.check_empty_results(WM.df_agg, config_data)

    # Check that there is only one user's data if no admin right
    if not has_slurmAdmin:
        if len(set(WM.df_agg_X.UserX)) > 1:
            raise ValueError(f"More than one user's logs was included, despite --slurmAdmin not used: {set(WM.df_agg_X.UserX)}")

    # WM.df_agg_X.to_pickle("testdata/df_agg_X_1.pkl") # DEBUGONLY used to test different steps offline

    return WM.df_agg_X, unfinished_jobs_service


def enrich_data(df: pd.DataFrame, fixed_params: dict, users_df: pd.DataFrame, GA: GA_tools, cluster_info: dict, db_params: DBSettings) -> pd.DataFrame:
    """
    Adds data about the carbon footprint, etc.
    :param df: [pd.DataFrame] The existing data we've extracted.
    :param fixed_params: [dict] The fixed parameters used.
    :param GA [GA_tools] A GA_tools object. 
    :return: [pd.DataFrame] The enriched data.
    """
    
    ### energy
    df = df.apply(GA.calculate_energies, axis=1)

    try:
        df['energy_failedJobs'] = np.where(df.StateX == 0, df.energy, 0)
    except AttributeError as err:
        print(f"enrich_data(): AttributeError: {err}")
        # TODO Explain this error, and what to do about it.
        return None  # or should we exit?
    
    ### Fetching Carbon Intensity
    postcode = cluster_info.get('postcode', None)
    ci_avg_data = {}
    if postcode:
        postcode = postcode[:3] # Taking only the first three letters from the postcode
        ci_service = CarbonIntensityService(postcode, db_params)
        ci_avg_data = ci_service.calc_day_average_CI(df.StartDatetimeX.min(), df.EndDatetimeX.max())

    ### carbon footprint
    for suffix in ['', '_memoryNeededOnly', '_failedJobs']:
        if ci_avg_data:
            df[f'carbonFootprint{suffix}'] = df.apply(
                lambda row: GA.calculate_carbonFootprint(row, suffix, ci_avg_data),
                axis=1
            )
        else: #use default CI value from cluster yaml
            df[f'carbonFootprint{suffix}'] = GA.calculate_carbonFootprint_default(df, f'energy{suffix}')

        # Context metrics (part 1)
        df[f'treeMonths{suffix}'] = df[f'carbonFootprint{suffix}'] / fixed_params['tree_month']
        df[f'cost{suffix}'] = df[f'energy{suffix}'] * fixed_params['electricity_cost']

    ### Context metrics (part 2)
    df['driving'] = df.carbonFootprint / fixed_params['passengerCar_EU_perkm']
    df['flying_NY_SF'] = df.carbonFootprint / fixed_params['flight_NY_SF']
    df['flying_PAR_LON'] = df.carbonFootprint / fixed_params['flight_PAR_LON']
    df['flying_NYC_MEL'] = df.carbonFootprint / fixed_params['flight_NYC_MEL']

    ### Add user details to jobs
    if users_df is None:
        print("No user info to add.")
        df2 = df
    else:
        df2 = pd.merge(df, users_df, left_on='UserX', right_on='User', how='inner')
        if len(df2) != len(df):
            # This basically raises an error if a user in the df isn't in the users_df,
            # which is obtained from the file listing the HPC users.
            raise ValueError("Not all users could be matched!")

    return df2


def summarise_data(df: pd.DataFrame) -> dict:

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
        ## We aggregate hierarchically to avoid duplicating efforts
        # With daily figures
        df_userdaily = agg_jobs(df, ['User', 'UID', 'Name', 'Group', 'Department', 'SubmitDate'])
        df_groupdaily = agg_jobs(df_userdaily, ['Group', 'Department', 'SubmitDate'])
        df_deptdaily = agg_jobs(df_groupdaily, ['Department', 'SubmitDate'])

        df_daily = agg_jobs(df_deptdaily, ['SubmitDate'])

        # Overall stats
        df_userActivity = agg_jobs(df_userdaily, ['User', 'UID', 'Name', 'Group', 'Department'])
        dict_userActivity = df_userActivity.set_index(["User"]).to_dict('index')

        df_groupActivity = agg_jobs(df_userActivity, ['Group', 'Department'])
        dict_groupActivity = df_groupActivity.groupby('Department').apply(lambda x: x.set_index('Group').to_dict(orient='index')).to_dict()
        # dict_groupActivity = df_groupActivity.groupby('Department').apply(lambda x: x.set_index('Group').to_dict(orient='index'), include_groups=False).to_dict()

        df_deptActivity = agg_jobs(df_groupActivity, ['Department'])
        dict_deptActivity = df_deptActivity.set_index(["Department"]).to_dict('index')

        df_overallStats = agg_jobs(df_daily)
        dict_overallStats = df_overallStats.iloc[0, :].to_dict()


        ## And put everything in a dict
        output = {
            "userDaily": df_userdaily,
            "groupDaily": df_groupdaily,
            "deptDaily": df_deptdaily,
            "daily": df_daily,
            "deptActivity": dict_deptActivity,
            "groupActivity": dict_groupActivity,
            'userActivity': dict_userActivity,
            "overallActivity": dict_overallStats,
        }

    else:
        df_userdaily = agg_jobs(df, ['SubmitDate'])
        df_overallStats = agg_jobs(df_userdaily)
        dict_overallStats = df_overallStats.iloc[0, :].to_dict()
        userID = df.UserX[0]

        output = {
            "userDaily": df_userdaily,
            'userActivity': {userID: dict_overallStats},
            "user": userID
        }

    # Some job-level statistics to plot distributions
    memoryOverallocationFactors = df.groupby('UserX')['memOverallocationFactorX'].apply(list).to_dict()
    memoryOverallocationFactors['overall'] = df.memOverallocationFactorX.to_numpy()
    output['memoryOverallocationFactors'] = memoryOverallocationFactors

    return output


def main_backend(config_data: dict, batches: list = None):
    '''
    :param config_data: dict
    :param batches: list containing pairs of start and end dates for each batch
    :return:
    '''
    ### Load cluster-specific info
    with (open(config_data['cluster_info_file'], "r")) as stream:
        try:
            cluster_info = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    ### Load fixed parameters
    with open(config_data['fixed_params_file'], "r") as stream:
        try:
            fixed_params = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    db_params = DBSettings(
        db_name=config_data['db_name'],
        user=config_data['db_user'],
        password=config_data['db_password'],
        host=config_data['db_host'],
        port=config_data['db_port']
    )

    # Get slurmAdmin data 
    has_slurmAdmin = True # get_slurmAdmin(args)

    ### Load user-specific data (if available)
    try:
        users_df = pd.read_csv(config_data['dashboard_users_file'])
    except FileNotFoundError:
        if has_slurmAdmin:
            raise ValueError("No user data available.")
        users_df = None

    GA = GA_tools(cluster_info, fixed_params)
    summary_stats_all = {}

    # Processing data in date-wise batches - particularly useful when pulling historical logs
    for dates_pair in batches:

        config_data['startDay'] = dates_pair[0] # Start date in current batch
        config_data['endDay'] = dates_pair[1] # End date in current batch

        df, unfinished_jobs_service = extract_data(config_data, has_slurmAdmin, cluster_info=cluster_info, db_params=db_params)
        df2 = enrich_data(df, fixed_params=fixed_params, users_df=users_df, GA=GA, cluster_info=cluster_info, db_params=db_params)
        summary_stats = summarise_data(df2) # TODO export and save df_userdaily regularly (as a more manageable database than all individual jobs?)
        process_and_store(summary_stats, db_params, unfinished_jobs_service)

        summary_stats_all = summary_stats_all | summary_stats

    return summary_stats_all


def process_and_store(summary_stats:dict, db_params:DBSettings, unfinished_jobs_service:UnfinishedJobsService) -> None:
    # Import aggregated data into a database
    data2db = DataSQLImport(
                summary_stats,
                db_params
            )
    try: 
        data2db.insert_data_into_db()
    except Exception as e:
        print(f"Error occurred while inserting data into database: {e}")
        return
    
    #only delete the finished jobs from ga_unfinished_jobs table after the new data has been successfully inserted
    unfinished_jobs_service.delete_resolved_unfinished_jobs()
    
        
