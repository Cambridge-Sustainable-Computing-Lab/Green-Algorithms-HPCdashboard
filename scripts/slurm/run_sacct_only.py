# ------------------------------------------------------------------
# This script uses ga_core.SacctClient to query SLURM directly using sacct.
# It also stores the received SLURM logs data in a binary data file to be used for upstream tasks.
#
# This script is intended to be used when the backend of the dashboard cannot be run on the same system
# that allows SLURM logs to be pulled from.
# In such a case, this script must be used to store the logs in a shared location (somewhere the backend can access it)
# using 'input_log_file_path=<path_to_binary_data_file>' in config.yaml, these can be processed by the backend.
# ------------------------------------------------------------------

import argparse
import datetime
import logging
import sys
from ga_core import SacctClient

logger = logging.getLogger(__name__)


def create_arguments():
    """
    Command line arguments for the script.
    :return: argparse object
    """
    parser = argparse.ArgumentParser(description='Run sacct command and save its output to a file.')

    default_endDay = datetime.date.today().strftime("%Y-%m-%d")  # today

    # Timeframe
    parser.add_argument('-S', '--startDay', type=str, required=True,
                         help='The first day to take into account, as YYYY-MM-DD.')
    parser.add_argument('-E', '--endDay', type=str,
                         help='The last day to take into account, as YYYY-MM-DD (default: today).',
                         default=default_endDay)
    # Output file
    parser.add_argument('-o', '--outFile', type=str, default='', required=True,
                         help='The name of the file to be written, for storing the output of sacct.')

    # (Optional) run sacct for all users - usually permitted with admin access
    parser.add_argument("-a", "--allUsers", help='Run sacct for all users (probably requires admin rights).',
                         required=False, dest='for_all_users', action='store_true')

    # (Optional) run as debug
    parser.add_argument("-d", "--debug", help='Debug mode', required=False, dest='debug', action='store_true')

    args = parser.parse_args()
    return args


def capture_sacct_output(args):
    """
    Using the command line arguments that the script receives, use SacctClient to pull logs within the given time span.
    Store the pulled logs in a binary data file in the required location.
    :param args: command line arguments containing startDay, endDay etc.
    """
    filename = args.outFile
    all_users = args.for_all_users  
    
    logger.info(f"Pulling sacct logs from {args.startDay} to {args.endDay} "
                f"(all users: {all_users})...")

    try:
        data = SacctClient.pull_logs_by_time(startDay=args.startDay, endDay=args.endDay, all_users=all_users)
    except Exception as e:
        logger.error(f"Failed to pull sacct logs: {e}")
        sys.exit(1)
        
    logger.debug(f"Output captured ({len(data)} bytes):")
    logger.debug(data)

    logger.info(f"Saving output to {filename}...")
    try:
        with open(filename, 'wb') as myfile:
            myfile.write(data)
    except OSError as e:
        logger.error(f"Failed to write output file '{filename}': {e}")
        sys.exit(1)

    logger.info(f"Done. Logs saved to {filename}")


def main():
    args = create_arguments()

    logging_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging_level)

    capture_sacct_output(args)


if __name__ == "__main__":
    main()