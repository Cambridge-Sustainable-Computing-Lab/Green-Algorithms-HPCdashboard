import argparse
import csv
import logging
import os

from ga_dashboard.grafana_ga.dashboard import GrafanaGADashboard
from ga_dashboard.grafana_ga.datasource import GrafanaGADataSource
from ga_dashboard.grafana_ga.folder import GrafanaGAFolder
from ga_dashboard.grafana_ga.password_gen import initialise_strict_password_generator
from ga_dashboard.grafana_ga.user import GrafanaGAUser


logger = logging.getLogger(__name__)

'''
Combines the usage of several of the scripts:

- Create data source
- Create Grafana folder to host the dashboards
- Import the dashboard JSON files into Grafana (and locate them in the Grafana folder created above)
- Create Grafana users and teams
- Add teams permission on the Grafana folder
'''

# NB The Grafana server must be running before you invoke this script. (e.g. % bin/grafana server)

# Example usage (run from top-level directory of repo):
#
# % python scripts/frontend/run_dashboard.py --admin_password <grafana_admin_password> \
#        --grafana_users_file ga_dashboard/samples/grafana_users_list.csv \
#        --db_name ga_db --db_user postgres --db_password <db_password> \
#        --input_dir ga_dashboard/dashboards
#        --name <name of your datasource>   <-- If not set, uses "grafana-postgresql-ga_db" 

# Or: as above but:
#    --input_dir scripts/end-to-end --name demo_datasource
# if you want to use that one instead.

#
# Note: the data source name must match the pluginId of the __inputs dictionary in the JSON file(s) used for the dashboards(s).
# 
# For example, if we had the JSON below, we would need "--name grafana-postgresql-datasource" in the script invocation
#  
# "__inputs": [
#   {
#     "name": "DS_GRAFANA-DEMO_DB",
#     "label": "demo_datasource",
#     "description": "",
#     "type": "datasource",
#     "pluginId": "grafana-postgresql-datasource",
#     "pluginName": "PostgreSQL"
#   }
#  ],

# Example setting grafana admin user password to whatever you want: 
# 
# ./grafana cli admin reset-admin-password <the admin password you want goes here>
# 
# (Called in grafana/bin directory)


def main():

    # Choose as appropriate
    default_grafana_users_file = 'ga_dashboard/samples/grafana_users_list.csv'

    argparser = argparse.ArgumentParser()
    argparser.add_argument("--name", "-n", help='Data source name', required=False, metavar='DS_NAME', default='grafana-postgresql-ga_db', dest='name')
    argparser.add_argument("--url", help='Grafana URL', required=False, metavar='URL', default='localhost:3000')
    argparser.add_argument("--admin_login", "-l", help='Grafana admin name', required=False, metavar='ADMIN_NAME', default='admin', dest='login')
    argparser.add_argument("--admin_password", "-a", help='Grafana admin password', required=True, metavar='ADMIN_PASS', dest='password')
    argparser.add_argument("--db_name", "-d", help='Database name', required=False, default='ga_db', dest='db_name')
    argparser.add_argument("--db_user", "-u", help='Database user name', required=False, default='postgres', dest='db_user')
    argparser.add_argument("--db_password", "-p", help='Database user password', required=True, dest='db_password')
    argparser.add_argument("--db_host", "-o", help='Database host', required=False, dest='db_host', default='localhost')
    argparser.add_argument("--db_port", help='Database port', required=False, default=5432)
    argparser.add_argument("--pg_version", help='PostgreSQL version', required=False, default=13)
    argparser.add_argument("--dashboard_folder_name", "-f", help='Name of the dashboard folder on Grafana', required=False, dest='dashboard_folder_name', default='Green Algorithms')
    argparser.add_argument("--input_dir", "-r", help='Dashboard JSON files directory, on disk', required=False, default = 'ga_dashboard/dashboards', metavar='INPUT_DIR', dest='input_dir')
    argparser.add_argument("--grafana_users_file", "-i", help='User list in CSV format', required=False, default=default_grafana_users_file, metavar='INPUT_FILE', dest='grafana_users_file')
    argparser.add_argument("--debug", help='Debug mode', required=False, action='store_true')

    args = argparser.parse_args()

    datasource_name = args.name
    grafana_url = args.url
    login = args.login
    password = args.password
    db_name = args.db_name
    db_user = args.db_user
    db_password = args.db_password
    db_host = args.db_host
    db_port = args.db_port
    pg_version = args.pg_version
    ga_dashboard_folder_name = args.dashboard_folder_name
    ga_dashboard_input_dir = args.input_dir # Where the dashboard JSON files are located, on disk.
    input_file = args.grafana_users_file
    debug = args.debug

    logging_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging_level)

    # Dashboard files directory
    if not os.path.isdir(ga_dashboard_input_dir):
        logger.error("Directory '" + ga_dashboard_input_dir + "' can't be found")
        exit(1)

    logger.info('###############')
    logger.info('# Data source #')
    logger.info('###############')
    ga_data_source = GrafanaGADataSource(login, password, grafana_url, db_name, db_user, db_password, db_host, db_port, pg_version, datasource_name)
    ga_data_source.create_datasource()

    logger.info('##################')
    logger.info('# Grafana folder #')
    logger.info('##################')
    ga_folder_import = GrafanaGAFolder(login, password, grafana_url, ga_dashboard_folder_name)
    ga_folder_import.get_folder()

    # Loop over dashboard files
    logger.info('########################')
    logger.info('# Grafana dashboard(s) #')
    logger.info('########################')
    for dashboard_filename in os.listdir(ga_dashboard_input_dir):
        if dashboard_filename.endswith('.json'):
            ga_dashboard = GrafanaGADashboard(login, password, grafana_url, ga_dashboard_input_dir, dashboard_filename, ga_folder_import.folder_uid)
            ga_dashboard.import_dashboard()
    

    logger.info('###########################')
    logger.info('# Grafana users and teams #')
    logger.info('###########################')
    grafana_user = GrafanaGAUser(login, password, grafana_url, ga_dashboard_folder_name)

    # Set up password generator
    PWG = initialise_strict_password_generator()

    with open(input_file, encoding='utf-8-sig', newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        for row in reader:
            # Create team (if needed)
            grafana_user.create_team(row['Group'])   #grafana_user.create_team(row['Team name'])

            # Generate password. It's up to you to decide what to do with it.
            grafana_password = PWG.generate()
            row['GrafanaPassword'] = grafana_password

            # Create user (if needed)
            row['org_id'] = 1 # Default organisation
            if (grafana_user.create_user(row)):
                logger.info(f"** Grafana password for user {row['User']} is {grafana_password} **")

    # Folder
    logger.info('##############################')
    logger.info('# Grafana folder permissions #')
    logger.info('##############################')
    grafana_folder = GrafanaGAFolder(login, password, grafana_url, ga_dashboard_folder_name)
    if not grafana_folder.find_ga_folder():
        grafana_folder.get_folder()
    grafana_folder.add_ga_folder_permissions(grafana_user.teams)



if __name__ == "__main__":
     main()