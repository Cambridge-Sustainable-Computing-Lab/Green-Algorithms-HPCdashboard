
import datetime
import os
from ga_dashboard.backend.workload_manager.slurm import WorkloadManager

def report_bugs(config_data, WM: WorkloadManager) -> None:
    if 'reportBug' in config_data.keys() or 'reportBugHere' in config_data.keys():
        log_name = str(datetime.datetime.now().timestamp()).replace(".", "_")

        scripts_dir = os.path.dirname(os.path.realpath(__file__))

        if 'reportBug' in config_data.keys():
            log_path = os.path.join(scripts_dir, '../error_logs', f'sacctOutput_{log_name}.csv')
            # Logging into a separate dir to write-protect the main one (not in place for now)
            # log_path = os.path.join(pathlib.Path(scripts_dir).parent.absolute(), 'GreenAlgorithms4HPC_errorLogs', f'sacctOutput_{log_name}.csv')
        else:
            # i.e. config_data['reportBugHere is True
            log_path = f'{config_data["userCWD"]}/sacctOutput_{log_name}.csv'

        os.makedirs(os.path.dirname(log_path), exist_ok=True) # Create error_logs dir if needed
        with open(log_path, 'wb') as f:
            f.write(WM.logs_raw)
        print(f"\nSLURM statistics logged for debugging: {log_path}\n")