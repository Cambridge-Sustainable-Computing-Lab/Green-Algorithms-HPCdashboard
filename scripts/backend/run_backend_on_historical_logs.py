import argparse
import maskpass  # to hide the passwords
from datetime import date
from datetime import timedelta

import sys
sys.path.append('../..')

# from ga_dashboard.backend.utils import validate_args
from ga_dashboard.backend.ga_tools import main_backend
from ga_dashboard.ga_config import GAConfig


if __name__ == "__main__":

    argparser = argparse.ArgumentParser(description="User-friendly interface to the different scripts.", 
                                        epilog="Uses sample config file by default.")
    
    argparser.add_argument("--config", help='Name of config file for your parameter values.', required=False, \
                            metavar='CONFIG_FILE', default="scripts/sample_config.txt", dest='config')

    args = argparser.parse_args()
    config_file = args.config

    # Parse config file
    ga_config = GAConfig(config_file)
    ga_config.ingest_config_file()

    # Ask for the database password
    if "db_password" not in ga_config.config_values.keys():
        ga_config.config_values["db_password"] = maskpass.askpass("Enter database admin user password: > ", mask="")

    # Overwrite start and end data  
    ga_config.config_values["startDay"] = "2000-01-01"
    # End date (Yesterday)
    ga_config.config_values["endDay"] = date.today() - timedelta(days = 1)

    ### Run backend to get data
    extracted_data = main_backend(ga_config.config_values)
