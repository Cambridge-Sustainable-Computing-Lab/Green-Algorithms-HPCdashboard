# ------------------------------------------------------------------
# Service to interact with the SLURM workload manager using the 'sacct' command.
# ------------------------------------------------------------------

import subprocess
import pandas as pd
import io

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
        Sacct command to pull logs for jobs that were active during the specified time range, meaning
        job.Start <= end_dt  AND  job.End >= start_dt (or job.End is empty)
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

    ## DEBUGGING/TESTING METHOD
    @classmethod
    def imitate_sacct_pull_by_time(cls, csv_bytes: bytes, startDay, endDay, delimiter: str = ',') -> bytes:
        """
        Imitate the sacct pull by time using a provided CSV file in bytes format. This is used for testing and development when real sacct data is not available.
        The CSV file should have the same format as the output of the sacct command.
        """
        try:
            df = pd.read_csv(io.StringIO(csv_bytes.decode('utf-8')), sep=delimiter)  

            df['Start_copy'] = pd.to_datetime(df['Start'], errors='coerce')
            df['End_copy'] = pd.to_datetime(df['End'], errors='coerce')

            start_dt = pd.to_datetime(startDay)
            end_dt = pd.to_datetime(endDay)

            filtered_df = (df[
                    (df['Start_copy'] <= end_dt) &
                    ((df['End_copy'] >= start_dt) | (df['End_copy'].isna()))
                    ]
                .copy()
                .drop(columns=['Start_copy', 'End_copy'])
                )

            if filtered_df.empty:
                return b''  # Return empty bytes if no data matches the filter criteria
            
            return filtered_df.to_csv(index=False).encode('utf-8')
        
        except Exception as e:
            print(f"Error occurred while imitating sacct pull by time: {e}")
            return None
