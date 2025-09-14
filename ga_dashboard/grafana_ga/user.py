import logging
from grafana_client.client import GrafanaClientError
from grafana_client.elements.user import User
from .base import GrafanaGABase


logger = logging.getLogger(__name__)


class GrafanaGAUser(GrafanaGABase):
    ''' Class used to create Grafana teams, Grafana user and assign the user to the team(s) '''

    def __init__(self, login:str, password:str, grafana_url:str, ga_dashboard_folder_name:str) -> None:
        super().__init__(login, password, grafana_url)
        self.ga_folder_name = ga_dashboard_folder_name
        self.teams = {}


    # NB Laurent's teams map to Loïc's groups
    def create_team(self, team_name:str) -> None:
        ''' Create a new Grafana team if it doesn't exist '''

        team = {"name": team_name } #, "email": "email@example.org"}
        try:
            grafana_team = self.grafana.teams.add_team(team)
            team = self.grafana.teams.get_team(grafana_team['teamId'])
            self.teams[team['uid']] = grafana_team
            if grafana_team and 'teamId' in grafana_team.keys():
                logger.info(f"> Team '{team_name}' (team ID: {grafana_team['teamId']}): created successfully")
                # e.g., Team 'group_1' (team ID: 18): created successfully
            else:
                logger.error(f"Team '{team_name}' creation doesn't seem to have been successful")
                exit(1)
        except GrafanaClientError as ex:
            if ex.status_code == 409:
                grafana_teams = self.grafana.teams.get_team_by_name(team_name)
                if grafana_teams and len(grafana_teams) > 0:
                    uid = grafana_teams[0]['uid']
                    self.teams[uid] = grafana_teams[0]
                logger.warning(f"Team '{team_name}' already exists: {ex.response['message']}")
            else:
                logger.error(f"ERROR during team creation: {ex}")
                exit(1)

        # Add team ID
        try:
            teams_list = self.grafana.teams.get_team_by_name(team_name)
            if teams_list and len(teams_list) > 0:
                uid = teams_list[0]['uid']
                self.teams[uid] = teams_list[0]
        except GrafanaClientError as ex:
            logger.error(f"ERROR during fetching of team '{team_name}': {ex}")


    def create_user(self, user_data:dict) -> any:
        ''' Create a new Grafana user if it doesn't exist.
            Return True if a new user is created 
        '''
        user_login_or_email = None

        if "User" in user_data:
            user_login_or_email = user_data["User"]
        elif "Email" in user_data:
            user_login_or_email = user_data["Email"]
        else:
            logger.error(f"Missing data for user. Data: {user_data}")
            exit(1)

        # Check existing user
        existing_user = self.check_existing_user(user_login_or_email)

        # Create user
        if existing_user and 'id' in existing_user.keys():
            teams = self.grafana.users.get_user_teams(existing_user['id'])
            user_teams = [x['name'] for x in teams]
            if user_teams:
                logger.warning(f"User '{user_login_or_email}' is already in Grafana (and in team(s) '{', '.join(user_teams)}')")
            else:
                logger.warning(f"User '{user_login_or_email}' is already in Grafana but is not member of a team")
        else:
            if (self.set_new_user(user_data)):
                return True
        return False
            

    def check_existing_user(self, user_login_or_email:str) -> User:
        '''
            Check if a Grafana user already exists or not
            @return: A grafana_client User (if found)
        '''
        try:
            existing_user = self.grafana.users.find_user(user_login_or_email)
            return existing_user
        except GrafanaClientError as ex:
            if ex.status_code == 404:
                # New user
                pass


    def set_new_user(self, user_data: dict) -> any:
        ''' Create a new Grafana user '''
        try:
            user = self.grafana.admin.create_user({
                "name": user_data['Name'], 
                "email": user_data['Email'], 
                "login": user_data['User'], 
                "password": user_data['GrafanaPassword'], 
                "OrgId": user_data['org_id']    
            })
        except GrafanaClientError as ex:
            logger.error(f"ERROR during user creation: {ex}")
            exit(1)

        # Add user to a team
        if user:
            logger.info(f"> User '{user_data['User']}' (user ID: {user['id']}): created successfully")
            self.add_to_team(user_data,user)
            return True


    def update_user(self, user:User, user_data: dict):
        ''' 
        Update an existing Grafana user. 
        
        Best to call check_existing_user() before this.
        '''

        # (Pdb) user
        # {'id': 41, 'uid': '', 'email': 'user1@example.com', 'name': 'John Smith', 'login': 'user1@example.com', 'theme': '', 'orgId': 1, 
        # 'isGrafanaAdmin': False, 'isDisabled': False, 'isExternal': False, 'isExternallySynced': False, 
        # 'isGrafanaAdminExternallySynced': False, 'authLabels': None, 'updatedAt': '2025-08-14T14:11:50+01:00', 
        # 'createdAt': '2025-08-14T11:08:44+01:00', 'avatarUrl': '', 'isProvisioned': False}
        #
        # (Pdb) user_data
        # {'User': 'uid_1', 'UID': '11111', 'Name': 'John Smith', 'Email': 'user1@example.com', 'Group': 'group_1', 
        # 'Department': 'Dept_3', 'GrafanaPassword': '*0IK^I^&UpO$2aX', 'org_id': 1}
        #
        # But some things in Grafana are read from Postgres e.g. $department will read what Postgres has for that user

        # Map between Grafana user dict and our user_data dict:
        user["name"] = user_data['Name'] 
        user["email"] = user_data['Email']
        user["login"] = user_data['User'] 
        user["OrgId"] = user_data['org_id']    
        
        # This will update the user's password even if they are currently logged in to grafana.
        # (Just trying to update the password by adding it to the dictionary doesn't work.)
        if not self.grafana.admin.change_user_password(user['id'], user_data['GrafanaPassword']):
            logger.error(f"ERROR unable to change password for user {user_data['User']}")
            exit(1)

        return self.grafana.users.update_user(user['id'], user)


    def add_to_team(self, user_data: dict, user: User) -> None:
        ''' Add Grafana user to team(s) '''
        try:
            for team_item in user_data['Group'].split(','):
                team_name = team_item.strip()
                team = self.grafana.teams.get_team_by_name(team_name)
                team_id = team[0]['id']
                self.grafana.teams.add_team_member(team_id, user['id'])
                logger.info(f"+ User '{user_data['User']}' (user ID: {user['id']}): added to team '{team_name}'")
        except GrafanaClientError as ex:
            logger.error(f"Can't find team '{team_name}' and/or can't add the user '{user_data['User']}' to the team: {ex}")
            exit(1)

