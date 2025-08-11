import argparse
import csv
import logging
import os

from ga_dashboard.grafana_ga.folder import GrafanaGAFolder
from ga_dashboard.grafana_ga.password_gen import initialise_strict_password_generator
from ga_dashboard.grafana_ga.user import GrafanaGAUser

logger = logging.getLogger(__name__)

"""
This script allows multiple users to be imported into Grafana, without using the web interface to add them.

Example user list for Grafana users. In CSV format.

Name,User,Email,Team name
User_1,uid_1,user1@example.com,Team 1
User_2,uid_2,user2@example.com,Team 1
etc.

Laurent says 'Team name' is mapped to 'Group' in the sample BACKEND csv file (anonymised).

Example (using Grafana admin defaults) from `GA4HPCdashboard` top directory:
python scripts/frontend/import_users.py --grafana_users_file docs/templates/sample_user_list.csv --admin_login admin --admin_password <password>

""" 

def main():
    argparser = argparse.ArgumentParser(description="Import users in user list file to Grafana.")
    argparser.add_argument("--grafana_users_file", "-i", help='User list in CSV format', required=True, metavar='INPUT_FILE', dest='grafana_users_file')
    argparser.add_argument("--url", help='Grafana URL', required=False, metavar='URL', default='localhost:3000')
    argparser.add_argument("--admin_login", "-l", help='Grafana admin name', required=False, metavar='ADMIN_NAME', default='admin', dest='login')
    argparser.add_argument("--admin_password", "-p", help='Grafana admin password', required=True, metavar='ADMIN_PASS', dest='password')
    argparser.add_argument("--debug", "-d", help='Debug mode', required=False, dest='debug', action='store_true')
    argparser.add_argument("--dashboard_folder_name", "-f", help='Name of the dashboard folder', required=False, dest='dashboard_folder_name', default='Green Algorithms')

    args = argparser.parse_args()

    input_file = args.grafana_users_file
    grafana_url = args.url
    login = args.login
    password = args.password
    debug = args.debug
    ga_dashboard_folder_name = args.dashboard_folder_name

    logging_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging_level)

    if not os.path.isfile(input_file):
        logger.error("File '" + input_file + "' can't be found")
        exit(1)

    # Set up password generator
    PWG = initialise_strict_password_generator()

    # current_grafana_user is the person corresponding to the Grafana admin/whoever is running this script.
    current_grafana_user = GrafanaGAUser(login, password, grafana_url, ga_dashboard_folder_name)

    with open(input_file, encoding='utf-8-sig', newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        for row in reader:

            # Create team (if needed)
            if "Group" in row:
                current_grafana_user.create_team(row['Group'])
            else:
                logger.error("No Group in users file!")
                exit(1)
            
            # Generate password. It's up to you to decide what to do with it.
            grafana_password = PWG.generate()
            row['GrafanaPassword'] = grafana_password
         
            # Create Grafana user (if needed)
            row['org_id'] = 1 # Default organisation
            if (current_grafana_user.create_user(row)):
                logger.info(f"** Grafana password for user {row['User']} is {grafana_password} **")

    # Folder
    grafana_folder = GrafanaGAFolder(login, password, grafana_url, ga_dashboard_folder_name)
    if not grafana_folder.find_ga_folder():
        grafana_folder.get_folder()
    grafana_folder.add_ga_folder_permissions(current_grafana_user.teams)


if __name__ == "__main__":
    main()
