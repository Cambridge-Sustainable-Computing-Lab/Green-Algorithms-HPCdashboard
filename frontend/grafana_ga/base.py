
from grafana_client import GrafanaApi


class GrafanaGABase:

    def __init__(self, login:str, password:str, grafana_url:str) -> None:
        base_url = "http://{}:{}@{}".format(login, password, grafana_url)
        self.grafana = GrafanaApi.from_url(base_url)
        self.check_grafana_is_on()


    def get_grafana_api(self) -> GrafanaApi:
        return self.grafana


    def check_grafana_is_on(self):
        try:
            res = self.grafana.health.check()
            if res["database"] != "ok":
                raise Exception("Grafana is not UP")
        except:
            raise Exception("Grafana is not ON")