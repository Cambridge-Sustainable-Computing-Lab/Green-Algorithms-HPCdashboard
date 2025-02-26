import os
import yaml
import datetime
import argparse
import pandas as pd
import numpy as np

# The online book (especially chapter 4) was used to help produce the
# structure of this package. (see https://py-pkgs.org/04-package-structure)
from ga_dashboard.backend.utils import check_empty_results #, simulate_mock_jobs
from ga_dashboard.backend.extract.slurm import WorkloadManager
from ga_dashboard.backend.data_sql_import import DataSQLImport

# print("Working dir1: ", os.getcwd())


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
        try:
            partition_info = self.cluster_info['partitions'][row.PartitionX]
        except KeyError as ke:
            print(f"calculate_energies(): KeyError: {ke}")
            return None

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

    def calculate_carbonFootprint(self, df, col_energy):
        return df[col_energy] * self.cluster_info['CI']


# def get_slurmAdmin(args:argparse.Namespace) -> bool:
#     print(type(args))
#     args_dict = args.__dict__
#     has_slurmAdmin = False
#     if 'db_name' in args_dict.keys():
#         has_slurmAdmin = True
#     elif 'slurmAdmin' in args_dict.keys():
#         if args.slurmAdmin:
#             has_slurmAdmin = True
#     return has_slurmAdmin


def extract_data(args:argparse.Namespace, has_slurmAdmin:bool, cluster_info) -> pd.DataFrame:

    if args.use_mock_agg_data: # DEBUGONLY Create/use some mock jobs with different users

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
        return pd.read_pickle(pickled_test_data)


    ### Pull usage statistics from the workload manager
    WM = WorkloadManager(args, cluster_info)
    WM.pull_logs()

    ### Log the output for debugging
    scripts_dir = os.path.dirname(os.path.realpath(__file__))
    if args.reportBug | args.reportBugHere:
        log_name = str(datetime.datetime.now().timestamp()).replace(".", "_")

        if args.reportBug:
            log_path = os.path.join(scripts_dir, '../error_logs', f'sacctOutput_{log_name}.csv')
            # Logging into a separate dir to write-protect the main one (not in place for now)
            # log_path = os.path.join(pathlib.Path(scripts_dir).parent.absolute(), 'GreenAlgorithms4HPC_errorLogs', f'sacctOutput_{log_name}.csv')
        else:
            # i.e. args.reportBugHere is True
            log_path = f'{args.userCWD}/sacctOutput_{log_name}.csv'

        os.makedirs(os.path.dirname(log_path), exist_ok=True) # Create error_logs dir if needed
        with open(log_path, 'wb') as f:
            f.write(WM.logs_raw)
        print(f"\nSLURM statistics logged for debugging: {log_path}\n")

    ### Turn usage logs into DataFrame
    WM.convert2dataframe()

    # And clean
    WM.clean_logs_df()
    # Check if there are any jobs during the period from this directory and with these jobIDs
    check_empty_results(WM.df_agg, args)

    # Check that there is only one user's data if no admin right
    if not has_slurmAdmin:
        if len(set(WM.df_agg_X.UserX)) > 1:
            raise ValueError(f"More than one user's logs was included, despite --slurmAdmin not used: {set(WM.df_agg_X.UserX)}")

    # WM.df_agg_X.to_pickle("testdata/df_agg_X_1.pkl") # DEBUGONLY used to test different steps offline

    return WM.df_agg_X


def enrich_data(df:pd.DataFrame, fixed_params:dict, users_df:pd.DataFrame, GA:GA_tools) -> pd.DataFrame:

    ### energy
    df = df.apply(GA.calculate_energies, axis=1)

    try:
        df['energy_failedJobs'] = np.where(df.StateX == 0, df.energy, 0)
    except AttributeError as err:
        print(f"enrich_data(): AttributeError: {err}")
        return None

    ### carbon footprint
    for suffix in ['', '_memoryNeededOnly', '_failedJobs']:
        df[f'carbonFootprint{suffix}'] = GA.calculate_carbonFootprint(df, f'energy{suffix}')
        # Context metrics (part 1)
        df[f'treeMonths{suffix}'] = df[f'carbonFootprint{suffix}'] / fixed_params['tree_month']
        df[f'cost{suffix}'] = df[f'energy{suffix}'] * fixed_params['electricity_cost'] # TODO use realtime electricity costs

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
            raise ValueError("Not all users could be matched!")

    return df2


def summarise_data(df:pd.DataFrame, args:argparse.Namespace) -> dict:

    if ( df is None ):
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



    df['SubmitDate'] = df.SubmitDatetimeX.dt.date  # TODO do it with real start time rather than submit day

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


def main_backend(args):
    '''

    :param args:
    :return:
    '''
    ### Load cluster-specific info
    with open(os.path.join(args.path_infrastructure_info, 'cluster_info.yaml'), "r") as stream:
        try:
            cluster_info = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    ### Load fixed parameters
    with open("data/fixed_parameters.yaml", "r") as stream:
        try:
            fixed_params = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    # Get slurmAdmin data 
    has_slurmAdmin = True # get_slurmAdmin(args)

    ### Load user-specific data (if available)
    try:
        users_df = pd.read_csv(os.path.join(args.path_infrastructure_info, 'users_list.csv'))
    except FileNotFoundError:
        if has_slurmAdmin:
            raise ValueError("No user data available.")
        users_df = None

    GA = GA_tools(cluster_info, fixed_params)

    df = extract_data(args, has_slurmAdmin, cluster_info=cluster_info)
    df2 = enrich_data(df, fixed_params=fixed_params, users_df=users_df, GA=GA)
    summary_stats = summarise_data(df2, args=args) # TODO export and save df_userdaily regularly (as a more manageable database than all individual jobs?)

    ## Store data into a database
    try:
        dict_keys = args.__dict__.keys() # This is when using command line arguments (Namespace)
    except:
        dict_keys = args._asdict().keys() # This is when using the debugging namedtuples TODO this a bit messy, should be cleaned up
    if 'db_name' in dict_keys:
        import_data_in_db(summary_stats, args)

    return summary_stats


def import_data_in_db(summary_stats:dict,args) -> None:
    # Import aggregated data into a database
    data2db = DataSQLImport(
                summary_stats,
                db_name=args.db_name,
                db_user=args.db_user,
                db_password=args.db_password,
                db_host=args.db_host,
                db_port=args.db_port
            )
    data2db.import_data()


if __name__ == "__main__":

    #### This is used for testing only ####

    from collections import namedtuple
    argStruct = namedtuple('argStruct',
                           'startDay endDay useCustomLogs use_mock_agg_data reportBug reportBugHere path_infrastructure_info')
    args = argStruct(
        startDay='2022-01-01',
        endDay='2023-06-30',
        useCustomLogs="", #"sacct_output_loic1.txt",
        use_mock_agg_data=True,
        reportBug=False,
        reportBugHere=False,
        path_infrastructure_info="../../../data/ourInfrastructure/CSD3", # change?
    )

    main_backend(args)

