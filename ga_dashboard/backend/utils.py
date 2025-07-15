import argparse
import datetime
import os
import sys
import random
import pandas as pd
import numpy as np
import yaml


class validate_args:
    """
    Class used to validate all the arguments provided.
    """
    # TODO add validation
    # TODO test these

    def _validate_dates(self, args):
        """
        Validates that `startDay` and `endDay` are in the right format and in the right order.
        """
        if args is None:
            raise Exception("null args!")
        
        # If we are using an existing file of sacct data, we don't need to specify dates.
        if args.useCustomLogs:
            return

        index = 0
        for x in [args.startDay, args.endDay]:
            if x is None:
                raise Exception(f"x is None: index {index}")
            try:
                datetime.datetime.strptime(x, '%Y-%m-%d')
            except ValueError:
                raise ValueError(f"Incorrect date format, should be YYYY-MM-DD but is: {x}")
            index += 1

        start = datetime.datetime.strptime(args.startDay, '%Y-%m-%d')
        end = datetime.datetime.strptime(args.endDay, '%Y-%m-%d')
        if start > end:
            raise ValueError(f"Start date ({args.startDay}) is after the end date ({args.endDay}).")

    def _validate_output(self, args):
        """
        Validates that --output is one of the accepted options.
        """
        list_options = ['terminal', 'html']
        if args.output not in list_options:
            raise ValueError(f"output argument invalid. Is {args.output} but should be one of {list_options}")

    def _validate_granularity(self, args):
        """
        Validates that --granularity is specified when --slurmAdmin is used.
        Validates that --granularity is one of the accepted options.
        """
        if (args.granularity is None)&(args.slurmAdmin):
            raise ValueError("--granularity argument is needed when --slurmAdmin flag is present.")

        if args.slurmAdmin:
            list_options = ['user', 'group', 'department', 'institution']
            if args.granularity not in list_options:
                raise ValueError(f"--granularity {args.granularity} invalid. Should be one of {list_options}.")

    def _validate_user(self, args):
        """
        Validates that --user is used if both --slurmAdmin is used and --granularity is not 'institution'.
        """
        if (args.slurmAdmin) & (args.granularity != 'institution') & (args.user is None):
            raise ValueError(f"--user argument missing. Needed with --slurmAdmin and --granularity {args.granularity}.")


    def _validate_db_conn(self, args):
        """
        Validates that the database exists and is accessible, using the provided "db" parameters.
        """
        import psycopg
        try:
            # Connect to an existing database
            conn = psycopg.connect(
                dbname=args.db_name,
                user=args.db_user,
                password=args.db_password,
                host=args.db_host,
                port=args.db_port
            )
            conn.close()
        except psycopg.OperationalError as err:
            raise(f'Error: Issue to connect to the database: {err}')


    def all_to_export(self, args):
        self._validate_dates(args)
        self._validate_output(args)
        self._validate_granularity(args)
        self._validate_user(args)


    def all_to_db(self, args):
        self._validate_dates(args)
        self._validate_db_conn(args)


def check_empty_results(df, args):
    """
    This is to check whether any jobs have been run in the period, and stop the script if not.
    :param df: [pd.DataFrame] Usage logs
    :param args: [argStruct] Named tuple of arguments used.
    """
    if len(df) == 0:
        if args.filterWD is not None:
            addThat = f' from this directory ({args.filterWD})'
        else:
            addThat = ''
        if args.filterJobIDs != 'all':
            addThat += ' and with these jobIDs'
        if args.filterAccount is not None:
            addThat += ' charged under this account'

        print(f'''

    You haven't run any jobs in that period (from {args.startDay} to {args.endDay}){addThat}.

        ''')
        sys.exit()


def simulate_mock_jobs(): # DEBUGONLY
    df_list = []
    for user in ['uid_1', 'uid_2', 'uid_3', 'uid_4', 'uid_5']:
        n_jobs = random.randint(500,800)
        data_dict = {
            'WallclockTimeX':[datetime.timedelta(minutes=random.randint(50,700)) for _ in range(n_jobs)],
            'ReqMemX':np.random.randint(4,130, size=n_jobs)*1.,
            'PartitionX':['yew']*n_jobs,
            'SubmitDatetimeX':[datetime.datetime(day=1,month=5,year=2023) + datetime.timedelta(days=random.randint(1,60)) for _ in range(n_jobs)],
            'StateX':np.random.choice([1,0], p=[.8,.2], size=n_jobs),
            'UIDX':['11111']*n_jobs,
            'UserX':[user]*n_jobs,
            'PartitionTypeX':['CPU']*n_jobs,
            'TotalCPUtime2useX':[datetime.timedelta(minutes=random.randint(50,5000)) for _ in range(n_jobs)],
            'TotalGPUtime2useX':[datetime.timedelta(seconds=0)]*n_jobs,
        }

        data_frame = pd.DataFrame(data_dict)
        data_frame['CPUhoursChargedX'] = data_frame.TotalCPUtime2useX / np.timedelta64(1, 'h')
        data_frame['GPUhoursChargedX'] = 0.
        data_frame['NeededMemX'] = data_frame.ReqMemX * np.random.random(n_jobs)
        data_frame['memOverallocationFactorX'] = data_frame.ReqMemX / data_frame.NeededMemX

        df_list.append(data_frame)

    return pd.concat(df_list)


def get_cluster_info(ns: argparse.Namespace, info_file: str) -> object:
    """
    Get the YAML object representation of a cluster info file.
    :param ns: [argparse.Namespace] Namespace representing the command-line arguments. Can be None
    :param info_file: [str] Name of info file, e.g., 'cluster_info.yaml'
    :return: [argparse.Namespace] The populated Namespace (args) object.

    NB The full path to the file can be specified in info_file if you set ns=None.
    """
    if ns and ns.path_infrastructure_info:
        file_path = os.path.join(ns.path_infrastructure_info, info_file)
    else:
        file_path = info_file

    with open(file_path, "r") as stream:
        try:
            cluster_info = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            cluster_info = None
    return cluster_info


def get_fixed_params(ns: argparse.Namespace, fp_file: str) -> object:
    """
    Get the YAML object representation of the fixed parameters file.
    :param ns: [argparse.Namespace] Namespace representing the command-line arguments.
    :param fp_file: [str] Name of fixed params file, e.g., 'cluster_info.yaml'
    :return: [argparse.Namespace] The populated Namespace (args) object.
    """
    with open(os.path.join(ns.path_infrastructure_info, fp_file), "r") as stream:
        try:
            fixed_params = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return fixed_params
