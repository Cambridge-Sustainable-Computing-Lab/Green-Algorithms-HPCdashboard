# sacct_file_pull.py
#
# Run the sacct command on a remote HPC server and store the results in a file.
# That file can be downloaded later, and passed to run_backend.sh with --useCustomLogs argument.
#
# You will want to use this script if, for example, you cannot run the rest of the Python code
# on that remote server.
#
# Example: 
# python run_sacct_only.py -S 2025-04-14 -E 2025-04-18 -a -o my_sacct_file.txt 

import argparse
import datetime
import logging
import subprocess

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

    # (Optional) run sacct for all users
    parser.add_argument("-a", "--allUsers", help='Run sacct for all users (probably requires admin rights).', required=False, dest='for_all_users', action='store_true')

    # (Optional) run as debug
    parser.add_argument("-d", "--debug", help='Debug mode', required=False, dest='debug', action='store_true')

    args = parser.parse_args()
    return args


def capture_sacct_output(args):

    # We want to run the sacct command on the remote HPC machine and save the result in a file on that machine.
    # It can then be downloaded for use with run_backend.py/.sh

    bash_com = [
        "sacct",
        "--starttime",
        args.startDay,  # format YYYY-MM-DD
        "--endtime",
        args.endDay,  # format YYYY-MM-DD
        "--format",
        "UID,User,JobID,JobName,Submit,Elapsed,Partition,NNodes,NCPUS,TotalCPU,CPUTime,ReqMem,MaxRSS,WorkDir,State,Account,AllocTres",
        "-P",
        "-L"  # All clusters
    ]

    filename = args.outFile

    if args.for_all_users:
        bash_com.append('--allusers')

    logger.debug("info SACCT CMD: " + str(bash_com))

    completed_processs = subprocess.run(bash_com, capture_output=True)
    data = completed_processs.stdout
    logger.debug("Output captured:")
    logger.debug(data)

    # Save the binary data into a file, for later ingestion by run_backend.py/.sh
    with open(filename, 'wb') as myfile:
        myfile.write(data)


def main():
    print("") # For neater output!

    args = create_arguments()

    logging_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging_level)
    
    capture_sacct_output(args)


if __name__ == "__main__":
    main()
