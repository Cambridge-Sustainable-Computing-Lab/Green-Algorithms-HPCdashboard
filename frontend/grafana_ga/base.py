import logging
from niquests.exceptions import ConnectionError
from grafana_client import GrafanaApi


logger = logging.getLogger(__name__)


class GrafanaGABase:
    ''' Base class holding the grafana_client GrafanaApi instance, the Grafana URL and the admin login/password'''

    def __init__(self, login:str, password:str, grafana_url:str) -> None:
        base_url = "http://{}:{}@{}".format(login, password, grafana_url)
        self.grafana = GrafanaApi.from_url(base_url)
        self.check_grafana_is_on()


    def get_grafana_api(self) -> GrafanaApi:
        '''
            Get GrafanaApi instance.
            @return: a GrafanaApi object
        '''
        return self.grafana


    def check_grafana_is_on(self):
        ''' Check that Grafana is setup correctly. '''
        try:
            res = self.grafana.health.check()
            if res["database"] != "ok":
                raise Exception("Grafana is not UP!")
        except ConnectionError as e:
            logger.error(f"Grafana is not ON!\n{e}")
            exit(0)