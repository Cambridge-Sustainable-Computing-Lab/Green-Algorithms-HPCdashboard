# Python script to create a more user-friendly interface to the other scripts.

# Place your values in the user section. A user config file. Else, defaults are used. Some may be boolean.

class Runner:

    def __init__(self):
        self.create_mydir()
        self.create_defaults_dict()
        

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
                    print(f"Error, duplicate script {client} !")
                    exit()
                else:
                    mydir[client] = directory 
        print(mydir)
        self.mydir = mydir


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
        pass


    def command_loop(self):
        pass


# e.g. python run.py myconfig.txt
if __name__ == "__main__":
    runner = Runner()
    runner.ingest_user_config_file()
    runner.command_loop()
    