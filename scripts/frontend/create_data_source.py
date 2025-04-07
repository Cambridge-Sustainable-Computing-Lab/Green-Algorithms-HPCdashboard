import argparse
import logging
from ga_dashboard.grafana_ga.datasource import GrafanaGADataSource

'''
Setup the PostgreSQL database connection ("data source") on Grafana.
'''


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--name", "-n", help='Data source name', required=False, metavar='DS_NAME', default='grafana-postgresql-ga_db', dest='name')
    argparser.add_argument("--url", help='Grafana URL', required=False, metavar='URL', default='localhost:3000')
    argparser.add_argument("--admin_login", "-l", help='Grafana admin name', required=False, metavar='ADMIN_NAME', default='admin', dest='login')
    argparser.add_argument("--admin_password", "-a", help='Grafana admin password', required=True, metavar='ADMIN_PASS', dest='password')
    argparser.add_argument("--db_name", "-d", help='Database name', required=True, dest='db_name')
    argparser.add_argument("--db_user", "-u", help='Database user name', required=True, dest='db_user')
    argparser.add_argument("--db_password", "-p", help='Database user password', required=True, dest='db_password')
    argparser.add_argument("--db_host", "-o", help='Database host', required=False, dest='db_host', default='localhost')
    argparser.add_argument("--db_port", help='Database port', required=False, default=5432)
    argparser.add_argument("--pg_version", help='PostgreSQL version', required=False, default=13)
    argparser.add_argument("--debug", help='Debug mode', required=False, action='store_true')

    args = argparser.parse_args()

    datasource_name = args.name
    grafana_url = args.url
    login = args.login
    password = args.password
    db_name = args.db_name
    db_user = args.db_user
    db_password = args.db_password
    db_host = args.db_host
    db_port = args.db_port
    pg_version = args.pg_version
    debug = args.debug

    logging_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging_level)

    ga_data_source = GrafanaGADataSource(login, password, grafana_url, db_name, db_user, db_password, db_host, db_port, pg_version, datasource_name)
    ga_data_source.create_datasource()

if __name__ == "__main__":
     main()