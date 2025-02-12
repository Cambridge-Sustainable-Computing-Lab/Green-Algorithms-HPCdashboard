import os, argparse, csv
import logging
from frontend.grafana_ga.user import GrafanaGAUser
from frontend.grafana_ga.folder import GrafanaGAFolder


logger = logging.getLogger(__name__)
      

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--input_file", "-i", help='User list in CSV format', required=True, metavar='INPUT_FILE', dest='input_file')
    argparser.add_argument("--url", help='Grafana URL', required=False, metavar='URL', default='localhost:3000')
    argparser.add_argument("--admin_login", "-l", help='Grafana admin name', required=False, metavar='ADMIN_NAME', default='admin', dest='login')
    argparser.add_argument("--admin_password", "-p", help='Grafana admin password', required=True, metavar='ADMIN_PASS', dest='password')
    argparser.add_argument("--debug", "-d", help='Debug mode', required=False, dest='debug', action='store_true')
    argparser.add_argument("--dashboard_folder", "-f", help='Name of the dashboard folder', required=False, dest='dashboard_folder', default='Green Algorithms')

    args = argparser.parse_args()

    input_file = args.input_file
    grafana_url = args.url
    login = args.login
    password = args.password
    debug = args.debug
    ga_dashboard_folder_name = args.dashboard_folder

    logging_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging_level)

    if not os.path.isfile(input_file):
        logger.error("File '"+input_file+"' can't be found")
        exit(1)

    grafana_user = GrafanaGAUser(login, password, grafana_url, ga_dashboard_folder_name)

    with open(input_file, encoding='utf-8-sig', newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        for row in reader:
            # Create team (if needed)
            grafana_user.create_team(row['Team name'])

            # Create user (if needed)
            row['org_id'] = 1 # Default organisation
            grafana_user.create_user(row)

    # Folder
    grafana_folder = GrafanaGAFolder(login, password, grafana_url, ga_dashboard_folder_name)
    if not grafana_folder.find_ga_folder():
        grafana_folder.get_folder()
    grafana_folder.add_ga_folder_permissions(grafana_user.teams)


if __name__ == "__main__":
     main()