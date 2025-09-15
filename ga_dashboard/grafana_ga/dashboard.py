import json
import logging
import os
from grafana_client.client import GrafanaClientError
from .base import GrafanaGABase


logger = logging.getLogger(__name__)


class GrafanaGADashboard(GrafanaGABase):
    ''' Class used to parse and import a Grafana dashboard (from a JSON file) '''

    def __init__(self, login:str, password:str, grafana_url:str, ga_dashboard_input_dir:str, ga_dashboard_filename:str, folder_uid:str) -> None:
        super().__init__(login, password, grafana_url)
        self.ga_dashboard_input_dir = ga_dashboard_input_dir
        self.ga_dashboard_filename = ga_dashboard_filename
        self.ga_dashboard_filepath = f"{ga_dashboard_input_dir}/{ga_dashboard_filename}"
        self.folder_uid = folder_uid
        self.dash_content = None


    def parse_json_to_content(self) -> None:
        ''' Parse the Dashboard JSON file into a Python dictionary. '''
        try:
            with open(self.ga_dashboard_filepath, "r") as f:
                json_content = f.read()
        except OSError as ex:
            logger.error(f"Reading file failed: {self.ga_dashboard_filepath}. Reason: {ex.strerror}")
            exit(1)

        try:
            self.dash_content = json.loads(json_content)
        except json.JSONDecodeError as ex:
            logger.error(f"Decoding JSON output from file failed: {json_content}. Reason: {ex}")
            exit(1)


    def import_dashboard(self) -> None:
        ''' Import a Dashboard from a JSON file to Grafana. '''
        if os.path.isfile(self.ga_dashboard_filepath):
            logger.info(f"Start to import dashboard from '{self.ga_dashboard_filepath}'")
            try:
                # Parse JSON file (dashboard content)
                self.parse_json_to_content()
                logger.info("Parsed.")
                
                # Fetch data source - NB This gets only the first one in the list (which may, or may not, have more). FIXME
                datasource_label = self.dash_content['__inputs'][0]['label']  # e.g., 'grafana-postgresql-ga_db'
                datasource = self.grafana.datasource.find_datasource(datasource_label)
                #logger.info(f"datasource: {datasource}")
                if 'id' not in datasource.keys():
                    logger.error(f"Can't find the data source '{datasource_label}'")
                    exit(1)
                datasource_uid = datasource['uid']

                # Update dashboard content & variables with the data source uid
                for panel in self.dash_content['panels']:
                    self.replace_datasource_uid_in_panel(panel,datasource_uid)
                    if 'panels' in panel.keys():
                        for subpanel in panel['panels']:
                            self.replace_datasource_uid_in_panel(subpanel,datasource_uid)
                # NOTE: not sure if the block below is still relevant
                for variable in self.dash_content['templating']['list']:
                    if 'datasource' in variable.keys():
                        variable['datasource']['uid'] = datasource_uid

                new_dash = {
                    "dashboard": self.dash_content,
                    "overwrite": True
                }
                
                # Add folder uid to the dashboard content
                new_dash["folderUid"] = self.folder_uid if self.folder_uid else 0
                
                # Dashboard
                new_dash["dashboard"]["id"] = None
                res = self.grafana.dashboard.update_dashboard(new_dash)
                if res["status"]: # TODO - check the status
                    logger.info(f"> Dashboard '{new_dash['dashboard']['title']}' has been created successfully")
                else:
                    logger.error(f"Dashboard '{new_dash['dashboard']['title']}' creation failed!")
            except GrafanaClientError as ex:
                logger.error(f"Can't fetch/update information from/to Grafana: {ex}")
                exit(1)
            except Exception as ex:
                logger.exception(f"Failed to load dashboard from: {self.ga_dashboard_filepath}. Reason: {ex}")
                exit(1)
        else:
            logger.error("Can't find the file '{self.ga_dashboard_filepath}'")
            exit(1)


    def replace_datasource_uid_in_panel(self, panel:dict, datasource_uid:str):
        '''
        Code used to replace the datasource variable (placeholded) by the datasource uid generated in the class GrafanaGADataSource

        Parameters
        ----------
        panel : dict. Represent the JSON structure of a dashboard panel. It could contain panels itself
        datasource_uid: str. Datasource unique ID generated in the class GrafanaGADataSource
        '''
        if 'datasource' in panel.keys():
            # self.dash_content['panels'][panel_idx]['datasource']['uid'] = datasource_uid
            panel['datasource']['uid'] = datasource_uid
        if 'targets' in panel.keys():
            for target in panel['targets']:
                if 'datasource' in target.keys():
                    target['datasource']['uid'] = datasource_uid