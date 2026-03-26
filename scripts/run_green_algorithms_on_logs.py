import argparse
import maskpass  # to hide the passwords
from datetime import date
from datetime import timedelta
from ga_dashboard.backend.ga_tools import LogsDataProcessor
from ga_dashboard.ga_config import GAConfig


if __name__ == "__main__":

    argparser = argparse.ArgumentParser(description="Script used to calculate Green Algorithms from HPC logs.",
                                        epilog="Requires a config file.")
    
    argparser.add_argument("--config", help='Name of config file for your parameter values.', required=True, \
                            metavar='CONFIG_FILE', dest='config')
    argparser.add_argument("--db_pass", help='Database password (optional, to avoid entering it in the prompt).', \
                            metavar='DB_PASS', dest='db_pass')

    args = argparser.parse_args()
    config_file = args.config
    db_pass = args.db_pass


    # Parse config file
    ga_config = GAConfig(config_file,db_pass)
    ga_config.ingest_config_file()

    # Ask for the database password
    if "db_password" not in ga_config.config_values.keys():
        ga_config.config_values["db_password"] = maskpass.askpass("Enter database admin user password: > ", mask="")

    # Overwrite start and end dates (with yesterday)
    yesterday = date.today() - timedelta(days = 1)
    if 'startDay' not in  ga_config.config_values.keys():
        ga_config.config_values["startDay"] = yesterday
    # End date (Yesterday)
    if 'endDay' not in  ga_config.config_values.keys():
        ga_config.config_values["endDay"] = yesterday

    ### Run backend to get data
    data_processor = LogsDataProcessor(ga_config.config_values)
    extracted_data = data_processor.run()
