import argparse
import maskpass  # to hide the passwords
from datetime import date
from datetime import timedelta
from ga_dashboard.backend.ga_tools import LogsDataProcessor
from ga_dashboard.ga_config import GAConfig

import datetime

if __name__ == "__main__":
    
    t_start = datetime.datetime.now()
    print(f"Running Green Algorithms on historical Logs")
    print(f"Historical logs processing started {t_start.strftime('%Y-%m-%d %H:%M:%S')}\n")

    argparser = argparse.ArgumentParser(description="Script used to calculate Green Algorithms from historical HPC logs.",
                                        epilog="Requires a config file.")
    
    argparser.add_argument("--config", help='Name of config file for your parameter values.', required=True, \
                            metavar='CONFIG_FILE', dest='config')
    argparser.add_argument("--db_pass", help='Database password (optional, to avoid entering it in the prompt).', \
                            metavar='DB_PASS', dest='db_pass')
    argparser.add_argument("--batch_size", help='Batch size in number of days. Default size is 30 days',\
                            metavar='Batch_SIZE', dest='batch_size')

    args = argparser.parse_args()
    config_file = args.config
    db_pass = args.db_pass
    
    if args.batch_size is None:
        print("WARNING: No batch size provided. Defaulting to 30 days.")
        batch_size = 30 # Defaulting to 30 days
    else:
        batch_size = int(args.batch_size)

    # Parse config file
    ga_config = GAConfig(config_file,db_pass)
    ga_config.ingest_config_file()

    # Ask for the database password
    if "db_password" not in ga_config.config_values.keys():
        ga_config.config_values["db_password"] = maskpass.askpass("Enter database admin user password: > ", mask="")

    # Overwrite start and end dates
    if 'startDay' not in  ga_config.config_values.keys():
        ga_config.config_values["startDay"] = "2000-01-01"
    # End date (Yesterday)
    if 'endDay' not in  ga_config.config_values.keys():
        ga_config.config_values["endDay"] = date.today() - timedelta(days = 1)                                          

    ### Run backend to get data
    data_processor = LogsDataProcessor(ga_config.config_values)
    extracted_data = data_processor.batch_run(batch_size = batch_size)

    t_end = datetime.datetime.now()
    print(f"\nHistorical logs processing completed {t_end.strftime('%Y-%m-%d %H:%M:%S')}")
