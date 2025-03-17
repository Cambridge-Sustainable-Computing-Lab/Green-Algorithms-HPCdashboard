import os,argparse
import logging
from grafana_ga.folder import GrafanaGAFolder
from grafana_ga.dashboard import GrafanaGADashboard

logger = logging.getLogger(__name__)


''' Import the dashboard JSON files (/frontend/dashboards) into Grafana (i.e. Grafana internal SQLite DB) '''


###############################################


def main():    

    script_path = os.path.dirname(os.path.realpath(__file__))
    default_dashboards_dir = f'{script_path}/dashboards/prod/'

    argparser = argparse.ArgumentParser()
    argparser.add_argument("--input_dir", "-i", help='Dashboard files directory', required=False, metavar='INPUT_DIR', default=default_dashboards_dir, dest='input_dir')
    argparser.add_argument("--url", help='Grafana URL', required=False, metavar='URL', default='localhost:3000')
    argparser.add_argument("--admin_login", "-l", help='Grafana admin name', required=False, metavar='ADMIN_NAME', default='admin', dest='login')
    argparser.add_argument("--admin_password", "-p", help='Grafana admin password', required=True, metavar='ADMIN_PASS', dest='password')
    argparser.add_argument("--dashboard_folder_name", "-f", help='Name of the dashboard folder', required=False, dest='dashboard_folder_name', default='Green Algorithms')
    argparser.add_argument("--debug", "-d", help='Debug mode', required=False, dest='debug', action='store_true')

    args = argparser.parse_args()

    input_dir = args.input_dir
    grafana_url = args.url
    login = args.login
    password = args.password
    debug = args.debug
    ga_dashboard_folder_name = args.dashboard_folder_name

    logging_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging_level)

    if not os.path.isdir(input_dir):
        logger.error("Directory '" + input_dir + "' can't be found")
        exit(1)

    ga_folder_import = GrafanaGAFolder(login, password, grafana_url, ga_dashboard_folder_name)
    ga_folder_import.get_folder()

    # Loop over dashboard files
    for dashboard_filename in os.listdir(input_dir):
        if dashboard_filename.endswith('.json'):
            ga_dashboard = GrafanaGADashboard(login, password, grafana_url,input_dir,dashboard_filename,ga_folder_import.folder_uid)
            ga_dashboard.import_dashboard()


if __name__ == "__main__":
     main()
