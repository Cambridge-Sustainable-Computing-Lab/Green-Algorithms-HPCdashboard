# ------------------------------------------------------------------
# Service to interact with the SLURM workload manager using the 'sacct' command.
# ------------------------------------------------------------------

import subprocess
import pandas as pd

class SacctService:
    """
    Service to interact with the SLURM workload manager using the 'sacct' command.
    Contains separate methods to pull logs in different contexts (by time, by JobID, etc.) and can be extended with more methods as needed.
    """

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
        try:
            bash_com_full = cls.bash_com + [
                "--starttime", startDay,
                "--endtime", endDay
            ]

            logs = subprocess.run(bash_com_full, capture_output=True)
            return logs.stdout   
        except Exception as e:
            print(f"Error occurred while pulling logs by time using sacct: {e}")
        finally:
            return None 

    @classmethod
    def pull_logs_by_jobid(cls, unfinished_jobs_df: pd.DataFrame | None = None):
        """
        Pull SLURM usage logs for jobs using sacct command. Can optionally fetch only specific JobIDs from a DataFrame.
        
        Args:
            unfinished_jobs_df: Optional DataFrame containing a column 'JobID'. If provided, only these jobs are fetched.
        """
        try: 
            if unfinished_jobs_df is not None and not unfinished_jobs_df.empty:
                jobid_list = unfinished_jobs_df['jobid'].astype(str).tolist()
                bash_com_full = cls.bash_com + ["--jobs", ",".join(jobid_list)]
            
                logs = subprocess.run(bash_com_full, capture_output=True)
                return logs.stdout
        except Exception as e:
            print(f"Error occurred while pulling logs by JobID using sacct: {e}")
        finally:
            return None