import argparse
import maskpass  # to hide the passwords
from datetime import date
from datetime import timedelta
from ga_dashboard.backend.ga_tools import main_backend
from ga_dashboard.ga_config import GAConfig


if __name__ == "__main__":

    argparser = argparse.ArgumentParser(description="Script used to calculate Green Algorithms from HPC logs.",
                                        epilog="Requires a config file.")
    
    argparser.add_argument("--config", help='Name of config file for your parameter values.', required=True, \
                            metavar='CONFIG_FILE', dest='config')

    args = argparser.parse_args()
    config_file = args.config

    # Parse config file
    ga_config = GAConfig(config_file)
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
    extracted_data = main_backend(ga_config.config_values)
