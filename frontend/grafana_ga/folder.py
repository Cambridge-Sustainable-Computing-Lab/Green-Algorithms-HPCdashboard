import logging

# On my machine (TM) grafana_client is in /opt/miniconda3/envs/py313/lib/python3.13/site-packages
# import sys
# sys.path.append("/opt/miniconda3/envs/py313/lib/python3.13/site-packages")

# in interpreter: 
# ['', 
# '/opt/miniconda3/envs/py313/lib/python313.zip', both
# '/opt/miniconda3/envs/py313/lib/python3.13',   both
# '/opt/miniconda3/envs/py313/lib/python3.13/lib-dynload', both
# '/opt/miniconda3/envs/py313/lib/python3.13/site-packages']  both

#  in code: 
# ['/Users/mg2216/repos/GA4HPCdashboard/frontend/grafana_ga', 
# '/opt/miniconda3/envs/py313/lib/python313.zip', both
# '/opt/miniconda3/envs/py313/lib/python3.13',   both
# '/opt/miniconda3/envs/py313/lib/python3.13/lib-dynload', both
# '/opt/miniconda3/envs/py313/lib/python3.13/site-packages']  both


import sys
# print(sys.path)
# sys.path.append('')
print(sys.path)
# exit

from grafana_client.client import GrafanaClientError
from .base import GrafanaGABase


logger = logging.getLogger(__name__)


class GrafanaGAFolder(GrafanaGABase):

    permission_levels = {
        1: {
            "role": "Viewer",
            "permission": 1
        },
        2: {
            "role": "Editor",
            "permission": 2
        },
        4: {
            "role": "Admin",
            "permission": 4
        }
    }

    default_permission_level = 1

    def __init__(self, login:str, password:str, grafana_url:str, ga_dashboard_folder_name:str) -> None:
        super().__init__(login, password, grafana_url)
        self.ga_folder_name = ga_dashboard_folder_name
        self.folder_uid = None
        self.teams = {}
        self.users = []
        self.levels = {}


    def find_ga_folder(self) -> bool:
        folders = self.grafana.folder.get_all_folders()
        for folder in folders:
            if folder['title'] == self.ga_folder_name:
                self.folder_uid = folder['uid']
                return True
        return False


    def get_folder(self) -> None:
        folder_name = self.ga_folder_name
        if self.find_ga_folder():
            logger.info(f"Folder '{folder_name}' already exists")
        else:
            try:
                self.grafana.folder.create_folder(title=folder_name)
                self.find_ga_folder()
                logger.info(f"> Folder '{folder_name}' successfully created")
            except GrafanaClientError as ex:
                logger.error(f"ERROR while creating the folder '{folder_name}': {ex}")
                exit(1)


    def get_current_teams_permissions(self) -> None:
        folder_permissions = self.grafana.folder.get_folder_permissions(self.folder_uid)
        for permission in folder_permissions:
            if 'teamId' in permission.keys():
                team_id =  permission['teamId']
                if team_id != 0:
                    permission_level = permission['permission']
                    self.teams[team_id] = {'teamId': team_id, 'permission': permission_level}
                    self.add_permission_level(permission_level)
            elif 'userId' in permission.keys():
                user_id =  permission['userId']
                if user_id != 0:
                    permission_level = permission['permission']
                    self.users.append({'userId': user_id, 'permission': permission_level})
                    self.add_permission_level(permission_level)


    def add_permission_level(self,permission_level:str) -> None:
        if permission_level not in self.levels.keys():
            self.levels[permission_level] = self.permission_levels[permission_level]


    def get_new_teams_permissions(self, teams:list) -> None:
        for team in teams:
            team_id = team['id']
            if not team_id in self.teams.keys():
                self.teams[team_id] = {'teamId': team_id, 'permission': self.default_permission_level}


    def add_ga_folder_permissions(self, teams: dict) -> None:
        # Fetch the list of users/teams/roles to add/update
        self.get_current_teams_permissions()
        self.get_new_teams_permissions(list(teams.values()))

        items = { 
            "items": []
        }
        for level in self.levels.values():
            items['items'].append(level)
        for team in self.teams.values():
           items['items'].append(team)
        for user in self.users:
           items['items'].append(user)
        try:
            if self.teams:
                response = self.grafana.folder.update_folder_permissions(self.folder_uid,items)
                if 'title' in response.keys():
                    logger.info(f"Folder '{response['title']}': {response['message']}")
                else:
                    logger.info(f"Folder: {response['message']}")
        except GrafanaClientError as ex:
            logger.error(f"Can't update folder permissions: {ex}")
            exit(1)