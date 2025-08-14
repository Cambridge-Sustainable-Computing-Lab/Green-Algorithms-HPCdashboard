import argparse
import csv
import logging
import os

from ga_dashboard.grafana_ga.folder import GrafanaGAFolder
from ga_dashboard.grafana_ga.user import GrafanaGAUser

logger = logging.getLogger(__name__)

"""
This script allows multiple users to be imported into Grafana, without using the web interface to add them.

Example user list in CSV format:

User,UID,Name,Email,Group,Department,Password
uid_1,11111,John Smith,user1@example.com,group_1,Dept_3,*0IK^I^&UpO$2aX
uid_2,22222,Sarah Jones,user2@example.com,group_1,Dept_3,yGg=kA-6v**7BS)
uid_3,33333,Tom Evans,user3@example.com,group_2,Dept_3,ibVvlpo$r7b0u
uid_4,44444,Lisa Bookbinder,user4@example.com,group_3,Dept_2,!3Q4o&%Fs5SE2
uid_5,55555,Ali Hassan,user5@example.com,group_4,Dept_1,qiY_pI%7BFz<JT


Laurent says 'Team name' is mapped to 'Group' in the sample BACKEND csv file (anonymised).

Example (using Grafana admin defaults) from `GA4HPCdashboard` top directory:
python scripts/frontend/import_users.py --dashboard_users_file docs/templates/sample_user_list.csv --admin_login admin --admin_password <password>

""" 

def main():
    argparser = argparse.ArgumentParser(description="Import users in user list file to Grafana.")
    argparser.add_argument("--dashboard_users_file", "-i", help='Location of dashboard user list, in CSV format', required=True, metavar='INPUT_FILE', dest='dashboard_users_file')
    argparser.add_argument("--url", help='Grafana URL', required=False, metavar='URL', default='localhost:3000')
    argparser.add_argument("--admin_login", "-l", help='Grafana admin name', required=False, metavar='ADMIN_NAME', default='admin', dest='login')
    argparser.add_argument("--admin_password", "-p", help='Grafana admin password', required=True, metavar='ADMIN_PASS', dest='password')
    argparser.add_argument("--debug", "-d", help='Debug mode', required=False, dest='debug', action='store_true')
    argparser.add_argument("--dashboard_folder_name", "-f", help='Name of the dashboard folder on Grafana', required=False, dest='dashboard_folder_name', default='Green Algorithms')

    args = argparser.parse_args()

    input_file = args.dashboard_users_file
    grafana_url = args.url
    login = args.login
    password = args.password  # The Grafana password of an admin user, running this script.
    debug = args.debug
    ga_dashboard_folder_name = args.dashboard_folder_name

    logging_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging_level)

    if not os.path.isfile(input_file):
        logger.error("File '" + input_file + "' can't be found")
        exit(1)

    # Set up password generator
    #PWG = initialise_strict_password_generator()

    # current_grafana_user is the person corresponding to the Grafana admin/whoever is running this script.
    current_grafana_user = GrafanaGAUser(login, password, grafana_url, ga_dashboard_folder_name)

    with open(input_file, encoding='utf-8-sig', newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        for row in reader:

            # Create team (if needed)
            if "Group" in row:
                current_grafana_user.create_team(row['Group']) # FIXME check team not exist first
            else:
                logger.error("No Group in users file!")
                exit(1)
             
            # Create Grafana user (if needed)
            row['org_id'] = 1 # Default organisation

            #logger.info("row")

            # Check if user exists, using both User and Email values
            user = current_grafana_user.check_existing_user(row["Email"])
            if not user:
                user = current_grafana_user.check_existing_user(row["User"])

            # If user exists, update it.
            # Else create it
            if user:
                logger.info("user exists")
                if current_grafana_user.update_user(user, row): # NB It doesn't update the password
                    logger.info(f"** Updated dashboard user {row['User']} on Grafana. **")
                else:
                    logger.error(f"** ERROR: unable to update dashboard user {row['User']} on Grafana. **")
                    exit(1) ## ?
            else:
                logger.info("user NOT exist")
                if (current_grafana_user.create_user(row)):
                    logger.info(f"** Added dashboard user {row['User']} to Grafana. **")
                else:
                    logger.error(f"** ERROR: unable to create dashboard user {row['User']} on Grafana. **")
                    exit(1)

    # Folder
    grafana_folder = GrafanaGAFolder(login, password, grafana_url, ga_dashboard_folder_name)
    if not grafana_folder.find_ga_folder():
        grafana_folder.get_folder()
    grafana_folder.add_ga_folder_permissions(current_grafana_user.teams)


if __name__ == "__main__":
    main()
