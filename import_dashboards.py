import os,argparse,json
import logging
from grafana_ga.folder import GrafanaGAFolder


logger = logging.getLogger(__name__)


def parse_json(json_file_path:str) -> json:
    try:
        with open(json_file_path, "r") as f:
            json_content = f.read()
    except OSError as ex:
        logger.error(f"Reading file failed: {json_file_path}. Reason: {ex.strerror}")
        exit(1)

    try:
        return json.loads(json_content)
    except json.JSONDecodeError as ex:
        logger.error(f"Decoding JSON output from file failed: {json_content}. Reason: {ex}")
        exit(1)


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
        logger.error("Directory '"+input_dir+"' can't be found")
        exit(1)

    ga_folder_import = GrafanaGAFolder(login, password, grafana_url, ga_dashboard_folder_name)
    ga_folder_import.get_folder()



    # Loop over dashboard files
    for dashboard_filename in os.listdir(input_dir):
        print(f"File '{dashboard_filename}'")
        if dashboard_filename.endswith('.json'):
            print(f"Dashboard file '{dashboard_filename}' is JSON")
            dashboard_file = f"{input_dir}/{dashboard_filename}"
            if os.path.isfile(dashboard_file):
                try:
                    # Parse JSON file (dashboard content)
                    dash_content = parse_json(dashboard_file)

                    # Fetch data source
                    datasource_label = dash_content['__inputs'][0]['label']
                    datasource = ga_folder_import.grafana.datasource.find_datasource(datasource_label)
                    if not 'id' in datasource.keys():
                        logger.error(f"Can't find the data source '{datasource_label}'")
                        exit(1)
                    datasource_uid = datasource['uid']
                    # Update dashboard content with the data source uid
                    for panel in dash_content['panels']:
                        if 'datasource' in panel.keys():
                            panel['datasource']['uid'] = datasource_uid
                    
                    new_dash = {
                        "dashboard": dash_content,
                        "overwrite": True
                    }
                    
                    # Add folder uid to the dashboard content
                    new_dash["folderUid"] = ga_folder_import.folder_uid if ga_folder_import.folder_uid else 0
                    
                    # Dashboard
                    new_dash["dashboard"]["id"] = None
                    res = ga_folder_import.grafana.dashboard.update_dashboard(new_dash)
                    if res["status"]: # TODO - check the status
                        logger.info(f"Dashboard '{new_dash['dashboard']['title']}' has been created successfully")
                    else:
                        logger.error(f"Dashboard '{new_dash['dashboard']['title']}' creation failed!")
                except Exception as ex:
                    msg = f"Failed to load dashboard from: {dashboard_filename}. Reason: {ex}"
                    logger.exception(msg)
                    exit(1)
            else:
                logger.error("Can't find the file '{dashboard_file}'")
                exit(1)

if __name__ == "__main__":
     main()