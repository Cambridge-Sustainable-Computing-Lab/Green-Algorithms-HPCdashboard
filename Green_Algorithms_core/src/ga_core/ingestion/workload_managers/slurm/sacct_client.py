# ------------------------------------------------------------------
# Contains the client for interacting with SLURM using 'sacct' command.
# ------------------------------------------------------------------

import subprocess

class SacctClient:
    """
    Client to interact with the SLURM workload manager using the 'sacct' command.
    Contains separate methods to pull logs in different contexts (by time, by JobID, etc.) and can be extended with more methods as needed.
    """

    bash_com = [
                "sacct",
                "--format",
                "UID,User,JobID,JobName,Submit,Start,End,Elapsed,Partition,NNodes,NCPUS,TotalCPU,CPUTime,"
                "ReqMem,MaxRSS,WorkDir,State,Account,AllocTres",
                "-P",
                "-L"  # All clusters
            ]
    
    @classmethod
    def pull_logs_by_time(cls, startDay, endDay, all_users=False):
        """
        Run the command line to pull usage from the workload manager by time.
        All Jobs started between the given start date and end date are pulled.
        More: https://slurm.schedmd.com/sacct.html

            Parameters:
            startDay (str): The start date in the format "YYYY-MM-DD".
            endDay (str): The end date in the format "YYYY-MM-DD".
            all_users (bool): Whether to pull logs for all users i.e. in case of Admin access. Default is False (pull logs for the current user only).
        """
        try:
            bash_com_full = cls.bash_com + [
                "--starttime", startDay,
                "--endtime", endDay
            ]

            if all_users:
                bash_com_full.append("--allusers")

            logs = subprocess.run(bash_com_full, capture_output=True)
            return logs.stdout   
        except Exception as e:
            print(f"Error occurred while pulling logs by time using sacct: {e}")
        finally:
            return None 