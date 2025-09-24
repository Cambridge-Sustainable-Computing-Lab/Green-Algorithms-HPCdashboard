import logging
from grafana_client.model import PersonalPreferences
from .base import GrafanaGABase

logger = logging.getLogger(__name__)


class GrafanaGAOrganization(GrafanaGABase):
    ''' Class used to get Grafana Organization '''

    default_theme = 'light'

    def __init__(self, login:str, password:str, grafana_url:str) -> None:
        super().__init__(login, password, grafana_url)


    def change_theme(self, new_default_theme:str=None):
        ''' 
        Change the default theme in Grafana. By default Grafana is setup with the "dark" theme,
        but we prefer to display the GA dashboard with the "light" theme.
        
        Parameters
        ----------
        new_default_theme : str. If not defined, the value of class variable 'self.default_theme' will be assigned.
        '''
        try:
            if not new_default_theme:
                new_default_theme = self.default_theme
            personal_pref = PersonalPreferences(theme=new_default_theme)
            self.grafana.organization.patch_preferences(personal_pref)
            logger.info(f"Grafana default theme changed to '{new_default_theme}'")
        except Exception as ex:
            logger.exception(f"Failed update Grafana default theme. Reason: {ex}")
            exit(1)