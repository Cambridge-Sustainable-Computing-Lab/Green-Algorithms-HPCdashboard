# ------------------------------------------------------------------
# Service constaining the main backend validation logic (any new validation logic should be added here)
# ------------------------------------------------------------------

import datetime

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
