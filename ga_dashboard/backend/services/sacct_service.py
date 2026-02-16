import subprocess
import pandas as pd

class SacctService:

    bash_com = [
                "sacct",
                "--allusers", # Diverges from GA4HPC; In GA4HPC '--allusers' is added only if user is an admin
                "--format",
                "UID,User,JobID,JobName,Submit,Start,End,Elapsed,Partition,NNodes,NCPUS,TotalCPU,CPUTime,"
                "ReqMem,MaxRSS,WorkDir,State,Account,AllocTres",
                "-P",
                "-L"  # All clusters
            ]
    
    @classmethod
    def pull_logs_by_time(cls, startDay, endDay):
        """
        Run the command line to pull usage from the workload manager by time.
        All Jobs started between the given start date and end date are pulled.
        More: https://slurm.schedmd.com/sacct.html
        """
        bash_com_full = cls.bash_com + [
            "--starttime", startDay,
            "--endtime", endDay
        ]

        logs = subprocess.run(bash_com_full, capture_output=True)
        return logs.stdout      

    # @classmethod
    # def pull_logs_by_jobid(cls, unfinished_jobs_df: pd.DataFrame | None = None):
    #     """
    #     Pull SLURM usage logs for jobs using sacct command. Can optionally fetch only specific JobIDs from a DataFrame.
        
    #     Args:
    #         unfinished_jobs_df: Optional DataFrame containing a column 'JobID'. If provided, only these jobs are fetched.
    #     """

    #     if unfinished_jobs_df is not None and not unfinished_jobs_df.empty:
    #         jobid_list = unfinished_jobs_df['JobID'].astype(str).tolist()
    #         bash_com_full = cls.bash_com + ["--jobs", ",".join(jobid_list)]
        
    #     logs = subprocess.run(bash_com_full, capture_output=True)
    #     return logs.stdout