import logging
from grafana_client.client import GrafanaClientError
from .base import GrafanaGABase


logger = logging.getLogger(__name__)


class GrafanaGADataSource(GrafanaGABase):

    def __init__(self, login:str, password:str, grafana_url:str, db_name:str, db_user:str, db_password:str, db_host:str, db_port:int = 5432, pg_version:int = 13, datasource_name:str = 'grafana-postgresql-ga_db', sslmode:str = 'disable') -> None:
        super().__init__(login, password, grafana_url)
        self.datasource_name = datasource_name
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.url = f'{db_host}:{db_port}'
        self.sslmode = sslmode

        pg_version_str = str(pg_version)
        if '.' in pg_version_str:
            pg_version_str = pg_version_str.replace('.','0')
        else:
            pg_version_str = pg_version_str + '00'
        self.pg_version = int(pg_version_str)
        self.build_datasource_content()


    def build_datasource_content(self) -> None:
        """ Build the JSON content used to create the data source """
        self.ds_content =  {
            "name": self.datasource_name,
            "type": "postgres",
            "url": self.url,
            "user": self.db_user,
            "access": "proxy", # Required to work
            "secureJsonData": {
                "password": self.db_password
            },
            "jsonData": {
                "database": self.db_name,
                "sslmode": self.sslmode, # disable/require/verify-ca/verify-full
                "postgresVersion": self.pg_version # 903=9.3, 904=9.4, 905=9.5, 906=9.6, 1000=10
            },
        }

    
    def create_datasource(self) -> None:
        """ Create the data source entry in Grafana"""
        datasource = None
        try:
            datasource = self.grafana.datasource.create_datasource(self.ds_content)
            logger.info(f"> Created data source: {datasource}")
        except GrafanaClientError as ex:
            # Data source already exist
            if ex.status_code == 409:
                logger.warning(f"Data source '{self.datasource_name}': {ex.response['message']}")
                datasource = self.grafana.datasource.get_datasource_by_name(self.datasource_name)
            # Other issue
            else:
                logger.error(f"ERROR during the data source creation: {ex}")
        
        if datasource:
            datasource_obj = self.grafana.datasource.get_datasource_by_name(self.datasource_name)
            if datasource_obj:
                ds_health = self.grafana.datasource.health(datasource_obj['uid'])
                if ds_health['status'] == 'OK':
                    logger.info(f"> Data source healthcheck: {ds_health['message']}")
                else:
                    logger.error(f"ERROR about the Data source health: {ds_health['message']}")
        else:
            logger.warning("The data source doesn't seem to have been created")