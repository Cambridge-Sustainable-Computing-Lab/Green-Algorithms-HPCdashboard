# Python script to add Dashboard users to the Postgres database and Grafana instance.

# Note: we assume that the scripts (including this one) are invoked from the top-level directory
# in the repository (i.e. the parent directory of scripts/).
# We also assumed that you installed the 'ga_dashboard' package from the top-level directory (e.g.: python -m pip install).

# All users added will be given read permission to the Grafana dashboard specified with the "dashboard_folder_name"
# in the config file.

import argparse
from collections import OrderedDict
from install_GAdashboard import GADashboardInstall 

class GADashboardAddUsers (GADashboardInstall):
    """
    Module used to add users to the Green Algorithms dashboard

    """

    def __init__(self, config_file: str, db_pass: str = None, grafana_pass: str = None) -> None:
        """
        Initialise GADashboardInstall object.
        
        Parameters
        ----------
        config_file : str. Name of the config file to use.
        db_pass: Database password
        grafana_pass: Grafana admin password
        """

        # Calling parent to set up self.config_file, self.db_pass, self.grafana_pass, self.got_db_password, self.got_grafana_admin_password
        super().init(config_file, db_pass, grafana_pass)

        # Scripts variables/config
        self.scripts = OrderedDict({
            "add_users_to_database.py": {
                "dir": "database",
                "title": "Add dashboard users to the Postgres database",
                "arg_list": ["db_name", "db_user", "db_password", "db_port", "db_host", "dashboard_users_file"]
            },
            "import_users.py": { 
                "dir" : "frontend", 
                "title": "Add dashboard users to Grafana",
                "arg_list": ["url", "admin_login", "admin_password", \
                             "dashboard_folder_name", "dashboard_users_file", "debug"]
            }
        })
  

# e.g. python scripts/add_users.py --config my_config.yaml
if __name__ == "__main__":

    argparser = argparse.ArgumentParser(description="Script to add users to the dashboard.")
    
    argparser.add_argument("--config", help='Name of config file for your parameter values.', required=True, \
                            metavar='CONFIG_FILE', dest='config')
    argparser.add_argument("--db_pass", help='Database password (optional, to avoid entering it in the prompt).', \
                            metavar='DB_PASS', dest='db_pass')
    argparser.add_argument("--grafana_pass", help='Grafana admin password (optional, to avoid entering it in the prompt).', \
                            metavar='GRAFANA_PASS', dest='grafana_pass')

    args = argparser.parse_args()
    config_file = args.config
    db_pass = args.db_pass
    grafana_pass = args.grafana_pass

    runner = GADashboardAddUsers(config_file, db_pass, grafana_pass)
    runner.run_pipeline()
