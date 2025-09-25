from ga_dashboard.ga_config import GAConfig


CONFIG_FILE = "configuration/examples/config__demo.txt"
DEMO_CONFIG = {
    'admin_login': 'admin',
	'cluster_info_file': 'configuration/examples/cluster_info__demo.yaml',
	'dashboard_folder_name': 'Green Algorithms Demo',
	'db_host': 'localhost',
	'db_name': 'ga_db',
	'db_port': '5432',
	'db_user': 'postgres',
	'db_script': 'ga_dashboard/database/ga_db.sql',
	'fixed_params_file': 'ga_dashboard/data/fixed_parameters.yaml',
	'input_dir': 'ga_dashboard/dashboards',
	'name': 'grafana-postgresql-ga_db',
	'pg_version': '13',
	'startDay': '2023-05-01',
	'endDay': '2023-06-30',
	'url': 'localhost:3000'
}


def test_ingest_config_file() -> None:
	'''
	Parse the config file and obtain any parameter values set by user.
	'''
	ga_config = GAConfig(CONFIG_FILE)
	ga_config.ingest_config_file(True)

	for item in DEMO_CONFIG.keys():
		expected_val = DEMO_CONFIG[item]
		assert ga_config.config_values[item] == expected_val
	