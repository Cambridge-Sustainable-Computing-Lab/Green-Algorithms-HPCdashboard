import argparse
import datetime

from backend.utils import validate_args
from backend import main_backend


def create_arguments():
    """
    Command line arguments for the tool.
    :return: argparse object
    """
    parser = argparse.ArgumentParser(description=f'Calculate your carbon footprint on the server.')

    default_endDay = datetime.date.today().strftime("%Y-%m-%d")  # today

    ## Timeframe
    parser.add_argument('-S', '--startDay', type=str,
                        help=f'The first day to take into account, as YYYY-MM-DD')
    parser.add_argument('-E', '--endDay', type=str,
                        help='The last day to take into account, as YYYY-MM-DD (default: today)',
                        default=default_endDay)

    ## How much information to process and display
    # parser.add_argument('--slurmAdmin', action='store_false',
    #                     help="Whether to run SLURM as admin and pull the logs from all users (provided it's available). Used by default.")
    # parser.add_argument('-o', '--output', type=str,
    #                     help="How to display the results, one of 'terminal' or 'html' (default: terminal)",
    #                     default='terminal')
    # parser.add_argument('-g', '--granularity', type=str,
    #                     help="The level of granularity of the report, needed with `--slurmAdmin`. " 
    #                          "One of 'user', 'group', 'department', 'institution'. "
    #                          "If 'user', 'group' or 'department', --user argument should be used.",
    #                     )
    # parser.add_argument('-u', '--user', type=str,
    #                     help="User ID for the user, (or user in the group/department of interest). "
    #                          "Only used if `--slurmAdmin`.",
    #                     )

    ## Filter out jobs
    # parser.add_argument('--filterCWD', action='store_true',
    #                     help='Only report on jobs launched from the current location.')
    parser.add_argument('--userCWD', type=str, help=argparse.SUPPRESS)
    # parser.add_argument('--filterJobIDs', type=str,
    #                     help='Comma separated list of Job IDs you want to filter on. (default: "all")',
    #                     default='all')
    # parser.add_argument('--filterAccount', type=str,
    #                     help='Only consider jobs charged under this account')
    # parser.add_argument('--customSuccessStates', type=str, default='',
    #                     help="Comma-separated list of job states. By default, only jobs that exit with status CD or \
    #                              COMPLETED are considered successful (PENDING, RUNNING and REQUEUD are ignored). \
    #                              Jobs with states listed here will be considered successful as well (best to list both \
    #                              2-letter and full-length codes. Full list of job states: \
    #                              https://slurm.schedmd.com/squeue.html#SECTION_JOB-STATE-CODES")
    # Required settings if the generated/aggregated data is to be imported into a database
    parser.add_argument('--db_name', type=str, help='Database name')
    parser.add_argument('--db_user', type=str, help='Database user name')
    parser.add_argument('--db_password', type=str, help='Database user password')
    parser.add_argument('--db_port', type=int, help='Database port', default=5432)
    parser.add_argument('--db_host', type=str, help='Database server host', default='localhost')

    ## Reporting bugs
    group1 = parser.add_mutually_exclusive_group()
    group1.add_argument('--reportBug', action='store_true',
                        help='In case of a bug, this flag exports the jobs logs so that you/we can investigate further. '
                             'The debug file will be stored in the shared folder where this tool is located (/error_logs), '
                             'to export it to your home folder, user `--reportBugHere`. '
                             'Note that this will write out some basic information about your jobs, such as runtime, '
                             'number of cores and memory usage.'
                        )
    group1.add_argument('--reportBugHere', action='store_true',
                        help='Similar to --reportBug, but exports the output to your home folder.')
    group2 = parser.add_mutually_exclusive_group()
    group2.add_argument('--useCustomLogs', type=str, default='',
                        help='This bypasses the workload manager, and enables you to input a custom log file of your jobs. \
                                 This is mostly meant for debugging, but can be useful in some situations. '
                             'An example of the expected file can be found at `example_files/example_sacctOutput_raw.txt`.')
    # Arguments for debugging only (not visible to users)
    # To ue arbitrary folder for the infrastructure information
    parser.add_argument('--useOtherInfrastuctureInfo', type=str, default='', help=argparse.SUPPRESS)
    # Uses mock aggregated usage data, for offline debugging
    group2.add_argument('--use_mock_agg_data', action='store_true', help=argparse.SUPPRESS)

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = create_arguments()

    if args.useOtherInfrastuctureInfo != '':
        args.path_infrastucture_info = args.useOtherInfrastuctureInfo
        print(f"Overriding infrastructure info with: {args.path_infrastucture_info}")
    else:
        args.path_infrastucture_info = 'data'


    ### Set the WD to filter on, if needed
    # if args.filterCWD:
    #     args.filterWD = args.userCWD
    #     print("\nNB: --filterCWD doesn't work with symbolic links (yet!)\n")
    # else:
    #     args.filterWD = None

    ### Validate input
    validate_args().all_to_db(args)

    ### Run backend to get data
    extracted_data = main_backend(args)