import datetime
import os
import pandas as pd
import numpy as np

from Green_Algorithms_core.src.ga_core.ingestion.workload_managers.base import BaseWorkloadManager
from Green_Algorithms_core.src.ga_core.utils import utils
from Green_Algorithms_core.src.ga_core.ingestion.workload_managers.slurm.sacct_client import SacctClient

class SlurmBase:
    """
    A utility class for processing and analyzing SLURM data from HPC cluster job schedulers. 
    Handles data transformation, parsing, cleaning, and metric calculations to support 
    cluster resource management and performance analysis.
    """
    def __init__(self, cluster_info):
        self.cluster_info = cluster_info
        self.unfinished_states = ['PENDING','RUNNING','SUSPENDED','UNKNOWN','PREEMPTED'] # States from SLURM documentation: https://slurm.schedmd.com/job_state_codes.html (as of 10 Feb 2026)

    def convert_to_GB(self, memory, unit):
        """
        Converts data quantity into GB.
        :param memory: [float] quantity to convert
        :param unit: [str] unit of `memory`, has to be one of ['M', 'G', 'K']
        :return: [float] memory in GB.
        """
        assert unit in ['M', 'G', 'K']
        if unit == 'M':
            memory /= 1e3
        elif unit == 'K':
            memory /= 1e6
        return memory

    def calc_ReqMem(self, x):
        """
        Calculates the total memory required when submitting the job.
        :param x: [pd.Series] one row of sacct output.
        :return: [float] total required memory, in GB.

        ReqMem Amount of memory requested; suffixed with 'c' if per CPU, 'n' if per node
        """
        mem_raw, n_nodes, n_cores = x['ReqMem'], x['NNodes'], x['NCPUS']

        if pd.isnull(mem_raw) or mem_raw == '0':
            unit = 'G'
            memory = 0
        elif mem_raw[-1] == 'n':
            unit = mem_raw[-2]
            memory = float(mem_raw[:-2]) * n_nodes
        elif mem_raw[-1] == 'c':
            unit = mem_raw[-2]
            memory = float(mem_raw[:-2]) * n_cores
        elif mem_raw[-1] in ['M', 'G', 'K']:
            unit = mem_raw[-1]
            memory = float(mem_raw[:-1])
        else:
            raise ValueError(f"Can't parse memory value: {mem_raw}. Please raise issue on GitHub.")

        return self.convert_to_GB(memory, unit)

    def clean_RSS(self, x):
        """
        Cleans the RSS value in sacct output.
        :param x: [NaN or str] the RSS value, either NaN or of the form '2745K'
        (optionally, just a number, we then use default_unit_RSS from cluster_info.yaml as unit).
        :return: [float] RSS value, in GB.
        """
        if pd.isnull(x.MaxRSS):
            # NB if no info on MaxRSS, we assume all memory was used
            memory = -1
        elif x.MaxRSS == '0':
            memory = 0
        else:
            assert isinstance(x.MaxRSS, str)
            # Special case for the situation where MaxRSS is of the form '154264' without a unit.
            if x.MaxRSS[-1].isalpha():
                memory = self.convert_to_GB(float(x.MaxRSS[:-1]), x.MaxRSS[-1])
            else:
                assert 'default_unit_RSS' in self.cluster_info, "Some values of MaxRSS don't have a unit. Please specify a default_unit_RSS in cluster_info.yaml"
                memory = self.convert_to_GB(float(x.MaxRSS), self.cluster_info.default_unit_RSS)

        return memory

    def clean_UsedMem(self, x):
        """
        Cleans the UsedMemory column
        :param x:
        :return: [float]
        """
        # NB when MaxRSS didn't store any values, we assume that "memory used = memory requested"
        return x.ReqMemX if x.UsedMem_ == -1 else x.UsedMem_

    def clean_partition(self, x):
        """
        Cleans the partition field, by replacing NaNs with empty string and selecting just one partition per job.
        :param x: data frame
        :return: [str] one partition or empty string

        x.Partition is [str] partition or comma-separated list of partitions
        """
        if pd.isnull(x.Partition):  # e.g. if it's NaN
            return ''

        L_partitions = x.Partition.split(',')
        if (x.WallclockTimeX.total_seconds() > 0) & (len(L_partitions) > 1):
            # Multiple partitions logged is only an issue for jobs that never started,
            # for the others, only the used partition is logged
            print(f"\n-!- WARNING: Multiple partitions logged on a job than ran: {x.JobID} - {x.Partition} (using the first one)\n")
        return L_partitions[0]

    def set_partitionType(self, x):
        assert x in self.cluster_info.partitions, f"\n-!- Unknown partition: {x} -!-\n"
        return self.cluster_info.partitions[x].type

    def parse_timedelta(self, x):
        """
        Parse a string representing a duration into a `datetime.timedelta` object.
        :param x: [str] Duration, as '[DD-HH:MM:]SS[.MS]'
        :return: [datetime.timedelta] Timedelta object
        """
        # Parse number of days
        day_split = x.split('-')
        if len(day_split) == 2:
            n_days = int(day_split[0])
            HHMMSSms = day_split[1]
        else:
            n_days = 0
            HHMMSSms = x

        # Parse ms
        ms_split = HHMMSSms.split('.')
        if len(ms_split) == 2:
            n_ms = int(ms_split[1])
            HHMMSS = ms_split[0]
        else:
            n_ms = 0
            HHMMSS = HHMMSSms

        # Parse HH,MM,SS
        last_split = HHMMSS.split(':')
        if len(last_split) == 3:
            to_add = []
        elif len(last_split) == 2:
            to_add = ['00']
        elif len(last_split) == 1:
            to_add = ['00', '00']
        else:
            raise ValueError(f"Can't parse {x}")
        n_h, n_m, n_s = list(map(int, to_add + last_split))

        return datetime.timedelta(
            days=n_days, hours=n_h, minutes=n_m, seconds=n_s, milliseconds=n_ms
        )

    def calc_realMemNeeded(self, x, granularity_memory_request):
        """
        Calculate the minimum memory needed.
        This is calculated as the smallest multiple of `granularity_memory_request` that is greater than maxRSS.
        :param x: [pd.Series] one row of sacct output.
        :param  granularity_memory_request: [float or int] level of granularity available when requesting memory on this cluster
        :return: [float] minimum memory needed, in GB.
        """
        minimum_mem = (int(x.UsedMem2_ / granularity_memory_request) + 1) * granularity_memory_request
        return minimum_mem if x.ReqMemX < x.UsedMem2_ else min(x.ReqMemX, minimum_mem)

    def calc_memory_overallocation(self, x):
        """
        Calculate the overallocation factor, as the ratio between memory requested and memory needed.
        
        :param x: [pd.Series] one row of sacct output.
        :return: [float] overallocation factor, with 1 meaning no overallocation.
        """
        # This is in case ReqMem is wrong or too low
        if x.NeededMemX == 0 and x.ReqMemX == 0:
            return 1.0
        elif x.NeededMemX == 0: # Edge Case - needs revisiting
            return 10.0  # Arbitrary high value to reflect the fact that there was a lot of overallocation.
        return min(1.0, x.ReqMemX / x.NeededMemX)

    def calc_CPUusage2use(self, x):
        if x.TotalCPUtime_.total_seconds() == 0:
            # This is when the workload manager actually didn't store real usage
            # NB: when TotalCPU=0, we assume usage factor = 100% for all CPU cores
            return x.CPUwallclocktime_

        assert x.TotalCPUtime_ <= x.CPUwallclocktime_
        return x.TotalCPUtime_

    def calc_GPUusage2use(self, x):
        if x.PartitionTypeX != 'GPU':
            return datetime.timedelta(0)
        if x.WallclockTimeX.total_seconds() > 0:
            assert x.NGPUS_ != 0
        return x.WallclockTimeX * x.NGPUS_  # NB assuming usage factor of 100% for GPUs

    def calc_coreHoursCharged(self, x):
        '''
        Split CPU and GPU core hours charged, depending on the partition.
        :param x:
        :return: [(float, float)]
        '''
        if x.PartitionTypeX == 'CPU':
            return x.CPUwallclocktime_ / np.timedelta64(1, 'h'), 0.
        else:
            return 0., x.WallclockTimeX * x.NGPUS_ / np.timedelta64(1, 'h')

    def clean_State(self, x, customSuccessStates_list):
        """
        Standardise the job's state, coding with {-1,0,1}
        :param x: [str] "State" field from sacct output
        :return: [int] in [-1,0,1]
        """
        # Codes are found here: https://slurm.schedmd.com/squeue.html#SECTION_JOB-STATE-CODES
        # self.args.customSuccessStates = 'TO,TIMEOUT'
        success_codes = ['CD', 'COMPLETED']
        if x in success_codes:
            codeState = 1
        elif x in customSuccessStates_list:
            # we allocate a lower value here so that when aggregating by jobID, the whole job keeps the flag
            # Otherwise a "cancelled" job could take over with StateX=0 for example
            codeState = -1
        else:
            codeState = 0

        return codeState

    def get_parent_jobID(self, x):
        """
        Get the parent job ID in case of array jobs
        :param x: [str] JobID of the form 123456789_0 (with or without '_0')
        :return: [str] Parent ID 123456789
        """
        job_id_parts = x.split('_')
        assert len(job_id_parts) <= 2, f"Can't parse the job ID: {x}"
        return job_id_parts[0]

class SlurmManager(SlurmBase, BaseWorkloadManager):

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

    
    ### Implements abstract methods from BaseWorkloadManager
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
            self.logs_raw = SacctClient.pull_logs_by_time(self.config_data['startDay'], self.config_data['endDay'], self.config_data['has_slurmAdmin'])                
    
    def clean_logs(self):
        """
        Clean the different fields of the usage logs.
        NB: the name of the columns ending with X need to be conserved, as they are used by the main script.
        """
        # self.logs_df_raw = self.logs_df.copy() # DEBUGONLY Save a copy of uncleaned raw for debugging mainly
        self.raw_logs = self.raw_logs_to_df()
        self.logs_df = self.filter_finished_jobs() # Keep only those jobs that have finished - i.e. contains a valid End date/ finished state

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

        ### Parse datetimes - Submit, Start, End
        self.logs_df['SubmitDatetimeX'] = self.logs_df.Submit.apply(
            lambda x: datetime.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S"))
        
        self.logs_df['StartDatetimeX'] = self.logs_df.Start.apply(
            lambda x: datetime.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S") if pd.notnull(x) else pd.NaT)
        
        self.logs_df['EndDatetimeX'] = self.logs_df.End.apply(
            lambda x: datetime.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S") if pd.notnull(x) else pd.NaT)

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
        self.df_agg = self.logs_df.groupby('single_jobID').agg({
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
            'StartDatetimeX': 'min',
            'EndDatetimeX': 'min',
            'WorkingDir_': 'first',
            'StateX': 'min',
            'Account_': 'first',
            'UIDX': 'first',
            'UserX': 'first'
        })

        self.df_agg.loc[self.df_agg.StateX == -1, 'StateX'] = 1 # Turn StateX==-1 into 1 (customSuccessStates are considered successful i.e. 1)

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
            granularity_memory_request=self.cluster_info.granularity_memory_request,
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
        return self.df_agg_X


    ### Other utility methods
    def raw_logs_to_df(self):
        """
        Convert raw logs output into a pandas dataframe - calling the static method convert2dataframe
        """
        delimiter = "," if 'useCustomLogs' in self.config_data.keys() and self.config_data['useCustomLogs'] != '' else "|"
        self.logs_df = utils.convert2dataframe(self.logs_raw, types = {'NNodes': 'int64', 'NCPUS': 'int64'}, delimiter=delimiter)


    def concat_logs_df(self, new_logs_df: pd.DataFrame):
        """
        Concatenate the existing logs dataframe with a new one, for example when we want to add finished jobs to previously-fetched logs.
        :param new_logs_df: [pd.DataFrame] new logs dataframe to concatenate with the existing one.
        """
        if self.logs_df is None:
            raise ValueError("logs_df is not initialised. Run pull_logs() and raw_logs_to_df() first.")
        
        self.logs_df = pd.concat([self.logs_df, new_logs_df], ignore_index=True)

    def filter_finished_jobs(self) -> pd.DataFrame:
        '''
        Filter finished jobs from the logs dataframe using the 'End' column if available, else the 'State' column.
        '''
        if 'End' in self.logs_df:
            mask = self.logs_df['End'].notna() & (self.logs_df['End'] != "Unknown")
        else: 
            ## NOTE: This is a temporary workaround for retrocompatibility since in earlier versions 'End' field was not fetched. Must be removed eventually.
            mask = ~self.logs_df['State'].isin(self.unfinished_states) 
        
        return self.logs_df[mask].copy()
        