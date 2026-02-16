import datetime
import os
import pandas as pd
from io import BytesIO

from ga_dashboard.backend.services.sacct_service import SacctService
from ga_dashboard.backend.workload_manager.WorkloadDataHandler import WorkloadDataHandler

class WorkloadManager(WorkloadDataHandler):

    def __init__(self, config_data:dict, cluster_info):
        """
        Methods related to the Workload manager
        :param config_data: [dict] Configuration data
        :param cluster_info: [dict] information about this specific cluster.
        """
        super().__init__(cluster_info=cluster_info)
        # self.args = args
        self.config_data = config_data

        # try:
        #     self.config_data = self.args.__dict__  # This is when using command line arguments (Namespace)
        # except Exception:
        #     self.config_data = self.args._asdict()  # This is when using the debugging namedtuples TODO this a bit messy, should be cleaned up

        self.logs_df = None
        self.df_agg_0 = None
        self.df_agg = None
        self.df_agg_X = None

    @staticmethod
    def convert2dataframe(logs_raw):
        """
        Convert raw logs output into a pandas DataFrame.
        Can be called independently with any raw logs.
        """
        logs_df = pd.read_csv(BytesIO(logs_raw), sep="|", dtype='str')
        for x in ['NNodes', 'NCPUS']:
            logs_df[x] = logs_df[x].astype('int64')
        return logs_df

    def pull_logs(self):
        """
        Run the command line to pull usage from the workload manager.
        More: https://slurm.schedmd.com/sacct.html
        """
        # Case where we can't run sacct, but use previously-obtained data instead
        if 'useCustomLogs' in self.config_data.keys() and self.config_data['useCustomLogs'] != '':
            message = "Overriding logs_raw with: "
            foundIt = False
            for sacctFileLocation in ['', 'testdata', 'error_logs']:
                if not foundIt:
                    try:
                        with open(os.path.join(sacctFileLocation, self.config_data['useCustomLogs']), 'rb') as f:
                            self.logs_raw = f.read()
                        message += f"{sacctFileLocation}/{self.config_data['useCustomLogs']}"
                        foundIt = True
                    except Exception:
                        pass
            if not foundIt:
                raise FileNotFoundError(f"Couldn't find {self.config_data['useCustomLogs']} \n "
                                        f"It should be either be in the testData/ or error_logs/ subdirectories, or the full path should be provided by --useCustomLogs.")
            print(message)

        # What we expect to be the usual case, where we run the sacct command.
        else:
            self.logs_raw = SacctService.pull_logs_by_time(self.config_data['startDay'], self.config_data['endDay'])                
    
    def raw_logs_to_df(self):
        """
        Convert raw logs output into a pandas dataframe - calling the static method convert2dataframe
        """
        self.logs_df = WorkloadManager.convert2dataframe(self.logs_raw)


    def clean_logs_df(self):
        """
        Clean the different fields of the usage logs.
        NB: the name of the columns ending with X need to be conserved, as they are used by the main script.
        """
        # self.logs_df_raw = self.logs_df.copy() # DEBUGONLY Save a copy of uncleaned raw for debugging mainly

        ### Calculate real memory usage
        self.logs_df['ReqMemX'] = self.logs_df.apply(self.calc_ReqMem, axis=1)

        ### Clean MaxRSS
        self.logs_df['UsedMem_'] = self.logs_df.apply(self.clean_RSS, axis=1)

        ### Parse wallclock time
        self.logs_df['WallclockTimeX'] = self.logs_df['Elapsed'].apply(self.parse_timedelta)

        ### Parse total CPU time
        # This is the total CPU used time, accross all cores.
        # But it is not reliably logged
        self.logs_df['TotalCPUtime_'] = self.logs_df['TotalCPU'].apply(self.parse_timedelta)

        ### Parse core-wallclock time
        # This is the maximum time cores could use, if used at 100% (Elapsed time * CPU count)
        self.logs_df['CPUwallclocktime_'] = self.logs_df['CPUTime'].apply(self.parse_timedelta)

        ### Number of GPUs
        # TODO double check that it includes multiple GPUs correctly
        if 'AllocTRES' in self.logs_df.columns:
            self.logs_df['NGPUS_'] = \
                self.logs_df.AllocTRES.str.extract(r'((?<=gres\/gpu=)\d+)', expand=False).fillna(0).astype('int64')
        else:
            print('Using old logs, "AllocTRES" information not available.')  # TODO: remove this after a while
            self.logs_df['NGPUS_'] = 0

        ### Clean partition
        # Make sure it's either a partition name, or a comma-separated list of partitions
        self.logs_df['PartitionX'] = self.logs_df.apply(self.clean_partition, axis=1)

        ### Parse submit datetime
        self.logs_df['SubmitDatetimeX'] = self.logs_df.Submit.apply(
            lambda x: datetime.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S"))

        ### Number of CPUs
        # e.g. here there is no cleaning necessary, so I just standardise the column name
        self.logs_df['NCPUS_'] = self.logs_df.NCPUS

        ### Number of nodes
        self.logs_df['NNodes_'] = self.logs_df.NNodes

        ### Job name
        self.logs_df['JobName_'] = self.logs_df.JobName

        ### Working directory
        self.logs_df['WorkingDir_'] = self.logs_df.WorkDir

        ### Username and UID
        self.logs_df['UIDX'] = self.logs_df.UID
        self.logs_df['UserX'] = self.logs_df.User

        ### State
        customSuccessStates_list = self.config_data.customSuccessStates.split(',') if 'customSuccessStates' in self.config_data.keys() else []
        self.logs_df['StateX'] = self.logs_df.State.apply(self.clean_State,
                                                          customSuccessStates_list=customSuccessStates_list)

        ### Pull jobID
        self.logs_df['single_jobID'] = self.logs_df.JobID.apply(lambda x: x.split('.')[0])

        ### Account
        if 'Account' in self.logs_df.columns:
            self.logs_df['Account_'] = self.logs_df.Account
        else:
            print('Using old logs, "Account" information not available.')  # TODO: remove this after a while
            self.logs_df['Account_'] = ''

        ### Aggregate per jobID
        self.df_agg_0 = self.logs_df.groupby('single_jobID').agg({
            'TotalCPUtime_': 'max',
            'CPUwallclocktime_': 'max',
            'WallclockTimeX': 'max',
            'ReqMemX': 'max',
            'UsedMem_': 'max',
            'NCPUS_': 'max',
            'NGPUS_': 'max',
            'NNodes_': 'max',
            'PartitionX': lambda x: ''.join(x),
            'JobName_': 'first',
            'SubmitDatetimeX': 'min',
            'WorkingDir_': 'first',
            'StateX': 'min',
            'Account_': 'first',
            'UIDX': 'first',
            'UserX': 'first',
        })

        ### Remove jobs that are still running or currently queued
        self.df_agg = self.df_agg_0.loc[self.df_agg_0.StateX != -2]

        ### Turn StateX==-2 into 1
        self.df_agg.loc[self.df_agg.StateX == -1, 'StateX'] = 1

        ### Replace UsedMem_=-1 with memory requested (for when MaxRSS=NaN)
        self.df_agg['UsedMem2_'] = self.df_agg.apply(self.clean_UsedMem, axis=1)

        ### Label as CPU or GPU partition
        self.df_agg['PartitionTypeX'] = self.df_agg.PartitionX.apply(self.set_partitionType)

        # Just used to clean up with old logs:
        if 'AllocTRES' not in self.logs_df.columns:
            self.df_agg.loc[self.df_agg.PartitionTypeX == 'GPU', 'NGPUS_'] = 1  # TODO remove after a while

        # Sanity check (no GPU logged for CPU partitions and vice versa)
        assert (self.df_agg.loc[self.df_agg.PartitionTypeX == 'CPU'].NGPUS_ == 0).all()
        foo = self.df_agg.loc[(self.df_agg.PartitionTypeX == 'GPU') & (self.df_agg.NGPUS_ == 0)]
        assert (foo.WallclockTimeX.dt.total_seconds() == 0).all()  # Cancelled GPU jobs won't have any GPUs allocated if they didn't start

        ## Check that there is no missing UID/User
        if self.df_agg.UIDX.isnull().sum() > 0:
            print(f"(!) WARNING: {self.df_agg.UIDX.isnull().sum()} jobs have missing UIDs")
        if self.df_agg.UserX.isnull().sum() > 0:
            print(f"(!) WARNING: {self.df_agg.UserX.isnull().sum()} jobs have missing Usernames")

        ### add the usage time to use for calculations
        self.df_agg['TotalCPUtime2useX'] = self.df_agg.apply(self.calc_CPUusage2use, axis=1)
        self.df_agg['TotalGPUtime2useX'] = self.df_agg.apply(self.calc_GPUusage2use, axis=1)

        ### Calculate core-hours charged
        self.df_agg[['CPUhoursChargedX', 'GPUhoursChargedX']] = self.df_agg.apply(self.calc_coreHoursCharged, axis=1, result_type='expand')

        ### Calculate real memory need
        self.df_agg['NeededMemX'] = self.df_agg.apply(
            self.calc_realMemNeeded,
            granularity_memory_request=self.cluster_info['granularity_memory_request'],
            axis=1)

        ### Add memory waste information
        self.df_agg['memOverallocationFactorX'] = self.df_agg.apply(self.calc_memory_overallocation, axis=1)

        # foo = self.df_agg[['TotalCPUtime_', 'CPUwallclocktime_', 'WallclockTimeX', 'NCPUS_', 'CoreHoursChargedCPUX',
        #                    'CoreHoursChargedGPUX', 'TotalCPUtime2useX', 'TotalGPUtime2useX']] # DEBUGONLY

        ### Filter on working directory
        if 'filterWD' in self.config_data.keys():
            if self.config_data['filterWD'] is not None:
                # FIXME: Doesn't work with symbolic links
                self.df_agg = self.df_agg.loc[self.df_agg.WorkingDir_ == self.config_data['filterWD']]
                # print(f'Filtered out {len(self.df_agg)-len(self.df_agg):,} rows (filterCWD={self.args.filterWD})') # DEBUGONLY

        ### Filter on Job ID
        self.df_agg.reset_index(inplace=True)
        self.df_agg['parentJobID'] = self.df_agg.single_jobID.apply(self.get_parent_jobID)

        if 'filterJobIDs' in self.config_data.keys():
            if self.config_data['filterJobIDs'] != 'all':
                list_jobs2keep = self.config_data['filterJobIDs'].split(',')
                self.df_agg = self.df_agg.loc[self.df_agg.parentJobID.isin(list_jobs2keep)]

        ### Filter on Account
        if 'filterJfilterAccountobIDs' in self.config_data.keys():
            if self.config_data['filterAccount'] is not None:
                self.df_agg = self.df_agg.loc[self.df_agg.Account_ == self.config_data['filterAccount']]

        self.df_agg_X = self.df_agg[[x for x in self.df_agg.columns if x[-1] == 'X']]
