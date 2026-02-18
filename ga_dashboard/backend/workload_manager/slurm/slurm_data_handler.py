import datetime
import pandas as pd
import numpy as np

class SlurmDataHandler:
    """
    A utility class for processing and analyzing workload data from HPC cluster job schedulers. 
    Handles data transformation, parsing, cleaning, and metric calculations to support 
    cluster resource management and performance analysis.
    """
    def __init__(self, cluster_info):
        self.cluster_info = cluster_info

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

        if pd.isnull(mem_raw):
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
                memory = self.convert_to_GB(float(x.MaxRSS), self.cluster_info['default_unit_RSS'])

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
        assert x in self.cluster_info['partitions'], f"\n-!- Unknown partition: {x} -!-\n"
        return self.cluster_info['partitions'][x]['type']

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
        # This is in case ReqMem is wrong or too low
        return 1. if x.ReqMemX < x.NeededMemX else x.ReqMemX / x.NeededMemX

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
        running_codes = ['PD', 'PENDING', 'R', 'RUNNING', 'RQ', 'REQUEUED']
        if x in success_codes:
            codeState = 1
        elif x in customSuccessStates_list:
            # we allocate a lower value here so that when aggregating by jobID, the whole job keeps the flag
            # Otherwise a "cancelled" job could take over with StateX=0 for example
            codeState = -1
        else:
            codeState = 0

        if x in running_codes:
            # running jobs are the lowest to be removed all the time
            # (if one of the subprocess is still running, the job gets ignored regardless of --customSuccessStates
            codeState = -2

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