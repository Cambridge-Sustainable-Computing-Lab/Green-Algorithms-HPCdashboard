import argparse
import maskpass  # to hide the passwords
import logging
from datetime import date
from datetime import timedelta
from ga_dashboard.backend.ga_tools import LogsDataProcessor
from ga_dashboard.ga_config import GAConfig
from ga_dashboard.backend.helpers import utils

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

    # set up logging
    log_file_path = ga_config.config_values.get("log_file", "run_green_algorithms_on_logs.log")
    debug_mode = ga_config.config_values.get("debug", False)

    # Initialize logging
    utils.setup_logging(log_file=log_file_path, debug=debug_mode)

    logging.info("run_green_algorithms_on_logs: Logging configured successfully.")

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
