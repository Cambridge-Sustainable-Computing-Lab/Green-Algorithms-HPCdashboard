# Python script to create a more user-friendly interface to the other scripts.

# Place your values in the user section. A user config file. Else, defaults are used. Some may be boolean.

# Note: we assume that the scripts are invoked from the top-level directory in the repository,
# i.e., the parent directory of scripts/

import subprocess
import sys

class Runner:

    def __init__(self):
        self.create_mydir()
        self.create_defaults_dict()
        self.create_arg_lists()
        

    def create_mydir(self):
        """
        Create `mydir` dictionary which stores, for each script, tne name of the 
        directory in which it resides. This will be used in constructing the path
        when we want to invoke a client script.

        e.g. mydir["add_users_to_database.py"] = "database"
        """
        files = {}

        # List of all client scripts in scripts/frontend:
        files["frontend"] = [ "create_data_source.py", "import_dashboards.py", "import_users.py", "run_dashboard.py" ]

        # List of all client scripts in scripts/database: 
        files["database"] = [ "add_users_to_database.py", "create_or_overwrite_database.sh", "import_mockup_aggregate.py" ]

        # List of all client scripts inscripts/backend:
        files["backend"] = [ "run_backend.py", "run_backend.sh", "run_sacct_only.py" ]

        # Now populate "mydir" dictionary. e.g. mydir["add_users_to_database.py"] = "database"
        mydir = {}
        for directory in files.keys():
            for client in files[directory]:
                # This should never happen, but check just in case:
                if client in mydir:
                    sys.exit(f"Error, duplicate client script {client} !")
                else:
                    mydir[client] = directory 
        print(mydir)
        self.mydir = mydir


    def create_arg_lists(self):
        '''
        Each script we invoke has an argument list.
        This function populates the arg_list dictionary, with key = script name,
        value = list of keyword argument names (without the leading --)
        '''
        arg_list = {}
        need_db_password = {}
        need_grafana_password = {}

        arg_list["add_users_to_database.py"] = ["db_name", "db_user", "db_password", "db_port", "db_host", "hpc_users_file"]
        need_db_password["add_users_to_database.py"] = True
        need_grafana_password["add_users_to_database.py"] = False
        
        self.arg_list = arg_list
        self.need_db_password = need_db_password


    def create_defaults_dict(self):
        '''
        Create "defaults" dictionary. Key = argument name, value = default value of argument.
        We don't store the leading -- before the argument name (e.g. --db_host), but add it later.

        NB (1) Some might not have defaults. (2) At least one argument is Boolean.
        '''
        defaults = {}
        defaults["admin_login"] = "admin" # Grafana admin user name.
        # defaults["allUsers"]  # Run sacct for all users (probably requires admin rights).
        # defaults["customSuccessStates"]
        defaults["dashboard_folder_name"] = "Green Algorithms"  # Name of the dashboard folder (on Grafana).
        defaults["db_host"] = "localhost"
        defaults["db_name"] = "ga_db"  # The name of the database to store your raw and enriched `sacct` data
        defaults["db_port"] = "5432"
        defaults["db_user"] = "postgres" # The default database user
        defaults["debug"] = False  # Debug mode. e.g. python myscript.py --debug
        # defaults["endDay"] = None # ???  The last day to take into account, as YYYY-MM-DD (default: today)
        # defaults["filterCWD"]   Not currently used. 
        # defaults["filterJobIDs"]  Not currently used. Comma-separated list of Job IDs you want to filter on. (default: "all")
        # defaults["filterAccount"]  Not currently used. 
        defaults["fixed_params_file"] = "ga_dashboard/data/fixed_parameters.yaml"  # The fixed parameters file to use
        defaults["grafana_users_file"] = None  # List of Grafana users, e.g., ga_dashboard/samples/grafana_users_list.csv
        # defaults["granularity"]  Not currently used. The level of granularity of the report, needed with `--slurmAdmin`. 
        defaults["hpc_users_file"] = None  # CSV file of (HPC) user data
        defaults["input_dir"] = "ga_dashboard/dashboards"  # Dashboard JSON files directory, on disk.
        defaults["input_log_file"] = None  # Logs data, e.g., ga_dashboard/samples/userDaily_mockMultiUsers_1.csv 
        defaults["name"] = "grafana-postgresql-ga_db" # Name of data source (on Grafana).
        defaults["outFile"] = None # The name of the file to be written, for storing the output of sacct.
        # defaults["output"] = None  # Not currently used.
        defaults["pg_version"] = "13"  # PostgreSQL version.
        # defaults["reportBug"]
        # defaults["reportBugHere"]
        # defaults["slurmAdmin"]
        defaults["startDay"] = None  # The first day to take into account, as YYYY-MM-DD
        defaults["url"] = "localhost:3000"  # Grafana URL (including port).
        defaults["useCustomLogs"] = None  # Bypass workload manager and input a custom log file of your jobs. Example: ga_dashboard/backend/example_files/example_sacctOutput_raw.txt
        # defaults["use_mock_agg_data"]  Not currently used?  Uses mock aggregated usage data, for offline debugging
        # defaults["useOtherInfrastructureInfo"]
        defaults["user"] = None # HPC username on slurm.
        # defaults["userCWD"]

        # db_password  # Database user password 
        # admin_password  # Grafana admin password.
    
        self.defaults = defaults
        # self.boolean_defaults = ...


    def ingest_user_config_file(self):
        '''
        Parse the config file and overwrite any default parameter values with values from that file.
        '''
        pass


    def command_loop(self):
        #pass
        subprocess.run(["python", "scripts/frontend/import_users.py", "-i", "ga_dashboard/samples/grafana_users_list.csv", "-p", "admin"])


    #def invoke_command()



# e.g. python run.py sample_config.txt
if __name__ == "__main__":
    runner = Runner()
    config_file = "sample_config.txt"
    #runner.ingest_user_config_file(config_file)
    runner.command_loop()

# database
#
# (py313) (base) mg2216@FL4P63QKYL GA4HPCdashboard % python scripts/database/add_users_to_database.py 
# usage: add_users_to_database.py [-h] --db_name DB_NAME --db_user DB_USER --db_password DB_PASSWORD --db_port DB_PORT --db_host DB_HOST --hpc_users_file HPC_USERS_FILE
# add_users_to_database.py: error: the following arguments are required: --db_name, --db_user, --db_password, --db_port, --db_host, --hpc_users_file
#
# (py313) (base) mg2216@FL4P63QKYL GA4HPCdashboard % python scripts/database/import_mockup_aggregate.py 
# usage: import_mockup_aggregate.py [-h] --input_log_file INPUT_FILE --db_name DBNAME --db_user DBUSER --db_password DBPASS --db_host DBHOST --db_port DBPORT
# import_mockup_aggregate.py: error: the following arguments are required: --input_log_file, --db_name, --db_user, --db_password, --db_host, --db_port
#
# (py313) (base) mg2216@FL4P63QKYL GA4HPCdashboard % sh scripts/database/create_or_overwrite_database.sh   <-- no help available. ?? change to python script??
#
# frontend
#
# (py313) (base) mg2216@FL4P63QKYL GA4HPCdashboard % python scripts/frontend/create_data_source.py 
# usage: create_data_source.py [-h] [--name DS_NAME] [--url URL] [--admin_login ADMIN_NAME] --admin_password ADMIN_PASS --db_name DB_NAME --db_user DB_USER --db_password DB_PASSWORD [--db_host DB_HOST] [--db_port DB_PORT] [--pg_version PG_VERSION] [--debug]
# create_data_source.py: error: the following arguments are required: --admin_password/-a, --db_name/-d, --db_user/-u, --db_password/-p
#
# (py313) (base) mg2216@FL4P63QKYL GA4HPCdashboard % python scripts/frontend/import_dashboards.py 
# usage: import_dashboards.py [-h] [--input_dir INPUT_DIR] [--url URL] [--admin_login ADMIN_NAME] --admin_password ADMIN_PASS [--dashboard_folder_name DASHBOARD_FOLDER_NAME] [--debug]
# import_dashboards.py: error: the following arguments are required: --admin_password/-p
#
# (py313) (base) mg2216@FL4P63QKYL GA4HPCdashboard % python scripts/frontend/import_users.py 
# usage: import_users.py [-h] --grafana_users_file INPUT_FILE [--url URL] [--admin_login ADMIN_NAME] --admin_password ADMIN_PASS [--debug] [--dashboard_folder_name DASHBOARD_FOLDER_NAME]
# import_users.py: error: the following arguments are required: --grafana_users_file/-i, --admin_password/-p
#
# (py313) (base) mg2216@FL4P63QKYL GA4HPCdashboard % python scripts/frontend/run_dashboard.py 
# usage: run_dashboard.py [-h] [--name DS_NAME] [--url URL] [--admin_login ADMIN_NAME] --admin_password ADMIN_PASS [--db_name DB_NAME] [--db_user DB_USER] --db_password DB_PASSWORD [--db_host DB_HOST] [--db_port DB_PORT] [--pg_version PG_VERSION]
#                        [--dashboard_folder_name DASHBOARD_FOLDER_NAME] [--input_dir INPUT_DIR] [--grafana_users_file INPUT_FILE] [--debug]
# run_dashboard.py: error: the following arguments are required: --admin_password/-a, --db_password/-p
#
# backend
#
# (py313) (base) mg2216@FL4P63QKYL GA4HPCdashboard % python scripts/backend/run_sacct_only.py 
# usage: run_sacct_only.py [-h] -S STARTDAY [-E ENDDAY] -o OUTFILE [-a] [-d]
# run_sacct_only.py: error: the following arguments are required: -S/--startDay, -o/--outFile
#
# (py313) (base) mg2216@FL4P63QKYL GA4HPCdashboard % python scripts/backend/run_backend.py -h
# usage: run_backend.py [-h] [-S STARTDAY] [-E ENDDAY] [--db_name DB_NAME] [--db_user DB_USER] [--db_password DB_PASSWORD] [--db_port DB_PORT] [--db_host DB_HOST] [--fixed_params_file FIXED_PARAMS_FILE] [--reportBug | --reportBugHere] [--useCustomLogs USECUSTOMLOGS]
#
# Calculate your carbon footprint on the server.
#
# options:
#  -h, --help            show this help message and exit
#  -S, --startDay STARTDAY
#                        The first day to take into account, as YYYY-MM-DD
#  -E, --endDay ENDDAY   The last day to take into account, as YYYY-MM-DD (default: today)
#  --db_name DB_NAME     Database name
#  --db_user DB_USER     Database user name
#  --db_password DB_PASSWORD
#                        Database user password
#  --db_port DB_PORT     Database port
#  --db_host DB_HOST     Database server host
#  --fixed_params_file FIXED_PARAMS_FILE
#                        The fixed parameters file to use
#  --reportBug           In case of a bug, this flag exports the jobs logs so that you/we can investigate further. The debug file will be stored in the shared folder where this tool is located (/error_logs), to export it to your home folder, user `--reportBugHere`. Note that
#                        this will write out some basic information about your jobs, such as runtime, number of cores and memory usage.
#  --reportBugHere       Similar to --reportBug, but exports the output to your home folder.
#  --useCustomLogs USECUSTOMLOGS
#                        This bypasses the workload manager, and enables you to input a custom log file of your jobs. This is mostly meant for debugging, but can be useful in some situations. An example of the expected file can be found at
#                        `backend/example_files/example_sacctOutput_raw.txt`.
#
# run_backend.sh is just a wrapper around this
#
