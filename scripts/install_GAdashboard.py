# Python script to install the Green Algorithms dashboard by:
# - Creating the database
# - Insert the HPC users list to the database
# - Setup Grafana:
#   > Create datasource (link database to Grafana)
#   > Create Grafana folder "Green Algorithms"
#   > Import Grafana dashboards (in the Green Algorithms" folder)
#   > Import Grafana users and teams (and generate users passwords)
#   > Setup Grafana folder permissions for the team

# Note: we assume that the scripts (including this one) are invoked from the top-level directory
# in the repository (i.e. the parent directory of scripts/).
# We also assumed that you installed the 'ga_dashboard' package from the top-level directory (e.g.: python -m pip install).


import argparse
import maskpass  # to hide the passwords
import subprocess
import sys
from collections import OrderedDict
from ga_dashboard.ga_config import GAConfig


class GADashboardInstall:
    """
    Module used to install the Green Algorithms dashboard
    1 - Create the database
    2 - Add the dashboard users list to the database
    3 - Setup Grafana:
        > Create datasource (link database to Grafana)
        > Create Grafana folder "Green Algorithms"
        > Import Grafana dashboards (in the Green Algorithms" folder)
        > Import dashboard users and teams into Grafana (and generate users passwords)
        > Setup Grafana folder permissions for the teams
    """

    def __init__(self, config_file: str) -> None:
        """
        Initialise GADashboardInstall object.
        
        Parameters
        ----------
        config_file : str. Name of the config file to use.
        """

        # Scripts variables/config
        self.scripts = OrderedDict({
            "create_or_overwrite_database.py": {
                "dir": "database", 
                "title": "Create database",
                "arg_list": ["db_name", "db_host", "db_port", "db_user", "db_password", "db_script"]
            },
            "add_users_to_database.py": {
                "dir": "database",
                "title": "Add HPC users in the database",
                "arg_list": ["db_name", "db_user", "db_password", "db_port", "db_host", "dashboard_users_file"]
            },
            "setup_frontend.py": { 
                "dir" : "frontend", 
                "title": "Setup Grafana",
                "arg_list": ["name", "url", "admin_login", "admin_password", "db_name", "db_user", "db_password", \
                            "db_host", "db_port", "pg_version", \
                            "dashboard_folder_name", "input_dir", "dashboard_users_file", "debug"]
            }
        })

        # We will only need to get these once at most per program operation.
        self.got_db_password = False
        self.got_grafana_admin_password = False

        # Fetch config file data
        self.config_file = config_file
        self.ingest_config_file()


    def get_command_components(self, client: str) -> list:
        '''
        Supply a list of the command-line components needed to invoke the script.

        Parameters
        ----------
        client : str. Name of the client script, e.g., "add_users_to_database.py"

        Returns
        -------
        list of individual command-line components
        e.g. ["python", "scripts/database/add_users_to_database.py", "db_name", "ga_db", "db_port", "5432", etc.]

        '''
        commander = "python"
        script_client_vars = self.scripts[client]
        path = "scripts" + "/" + script_client_vars['dir'] + "/" + client
        components = [commander, path]

        for item in script_client_vars['arg_list']:
            value = None

            # Get a value from the config file
            if self.ga_config_values and item in self.ga_config_values:
                value = self.ga_config_values[item]
            else:
                print(f"\nERROR: no value found for {item}, needed by {client}")
                print("Please add one to your config file.")
                sys.exit("Exiting...")

            # Optional parameters
            if item == "useCustomLogs" and not value:
                continue
            if item == "debug":
                if value == "True":
                    components.append("--debug")
                continue
            if item == "create_password_file":
                if value == "True":
                    components.append("--create_password_file")
                continue

            # Value can't be None or "None", as that isn't very helpful
            if ( value and value != "None" ):
                components.append(f"--{item}")  # <- Put the leading "--" needed for each parameter name, e.g., "--db_name". 
                components.append(value)        # <- e.g., "ga_db"
            else:
                print(f"\nERROR: 'None' is not a valid value for {item}, needed by {client}")
                print("Please add one to your config file.")
                sys.exit("Exiting...")

        # Show list of components to user.
        # We obscure the Grafana and PostgreSQL passwords.
        print()
        for compnum in range(len(components)):
            comp = components[compnum]
            if compnum == 0:
                print(f" {comp}", end='')
                continue
            prevcomp = components[compnum-1]
            if prevcomp in ["--db_password", "--admin_password"]:
                print(" ********", end='')
            else:
                print(f" {comp}", end='')
        
        print("\n", flush=True)

        #print(components)
        return(components)
        

    def ingest_config_file(self) -> None:
        '''
        Parse the config file and obtain any parameter values set by user.
        '''
        ga_config = GAConfig(self.config_file)
        ga_config.ingest_config_file()
        self.ga_config_values = ga_config.config_values


    def get_grafana_password(self) -> None:
        '''
        Get Grafana admin password, if not already supplied.
        '''
        self.ga_config_values["admin_password"] = maskpass.askpass("Enter Grafana admin password: > ", mask="")
        self.got_grafana_admin_password = True


    def get_db_password(self) -> None:
        '''
        Get database admin password, if not already supplied.
        '''
        self.ga_config_values["db_password"] = maskpass.askpass("Enter database admin user password: > ", mask="")
        self.got_db_password = True


    def run_pipeline(self) -> None:
        '''
        Run pipeline
        '''
        if "admin_password" not in self.ga_config_values:
            self.get_grafana_password()
        if "db_password" not in self.ga_config_values:
            self.get_db_password()

        # for script in ["create_or_overwrite_database.py", "add_users_to_database.py", "setup_frontend.py"]:
        scripts_list = self.scripts.keys()
        scripts_count_total = len(scripts_list)
        scripts_count = 1
        for script in scripts_list:
            print(f'\n\n##### Script {scripts_count}/{scripts_count_total} - {self.scripts[script]["title"]} #####')
            scripts_count += 1
            command_components = self.get_command_components(script)
            if ( command_components is None ):
                print("Error in components")
            else:
                subprocess.run(command_components)


# e.g. python scripts/install_GAdashboard.py --config my_config.txt
if __name__ == "__main__":

    argparser = argparse.ArgumentParser(description="Script to initialise the database storing the Green Algorithms data and setup Grafana.")
    
    argparser.add_argument("--config", help='Name of config file for your parameter values.', required=True, \
                            metavar='CONFIG_FILE', dest='config')

    args = argparser.parse_args()
    config_file = args.config

    runner = GADashboardInstall(config_file)
    runner.run_pipeline()
