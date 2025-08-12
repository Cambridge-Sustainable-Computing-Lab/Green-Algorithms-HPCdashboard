import os
import re
import maskpass
import psycopg


class GAConfig:
    # Class to parse, store and validate the configuration data into a dictionary

    # Mandatory parameters
    config_attr = {
        'admin_login': { 'expected_type': 'string' },
        'cluster_info_file': { 'expected_type': 'path' },
        'dashboard_folder_name': { 'expected_type': 'string' },
        'dashboard_users_file': { 'expected_type': 'string' },
        'db_host': { 'expected_type': 'string' },
        'db_name': { 'expected_type': 'string' },
        'db_port': { 'expected_type': 'numeric' },
        'db_script': { 'expected_type': 'string' },
        'db_user': { 'expected_type': 'string' },
        'fixed_params_file': { 'expected_type': 'path' },
        'input_dir': { 'expected_type': 'path' },
        'name': { 'expected_type': 'string' },
        'outFile': { 'expected_type': 'string' }, # Path doesn't exist yet
        'pg_version': { 'expected_type': 'numeric' },
        'url': { 'expected_type': 'string' }
    }

    extra_attr = {
        'startDay': { 'expected_type': 'date (YYYY-MM-DD)' },
        'endDay': { 'expected_type': 'date (YYYY-MM-DD)' }
    }

    def __init__(self, config_file:str):
        self.config_file = config_file
        # Default value
        self.config_values = {
            'debug': False
        }


    def ingest_config_file(self) -> None:
        '''
        Parse the config file and obtain any parameter values.

        Parameters
        ----------
        config_file : str. Name of the config file to use.
        '''

        # Read the file into memory (it's not enormous).
        with open(self.config_file, 'r') as infile:
            content = infile.readlines()

        # Examine each line of the file.
        for line in content:
            # print(line, end="")

            # Skip over whitespace-only lines:
            if line.isspace():
                continue

            # Skip over comments:
            if line.startswith("#"):
                continue 

            # Line should be like: db_name = ga_db
            # Or: test = This is a test.
            pieces = line.split(sep=" = ")
            if len(pieces) != 2:
                print(f"ERROR: line is {line}")
                continue
            arg = pieces[0]
            self.config_values[arg] = pieces[1].rstrip()  # Remove trailing whitespace and new line characters

        # Add database password
        self._get_db_password()
        # Check values
        self._check_config_values()
        # Check DB connection
        self._validate_db_conn()


    def _check_config_values(self) -> None:
        '''
        Check the configuration parameters.
        '''
        user_config_items = self.config_values.keys()
        invalid_items = {}
        missing_items = []
        # Check mandatory parameters
        for conf_param in self.config_attr.keys():
            if conf_param not in user_config_items:
                missing_items.append(conf_param)
            else:
                # Validate types
                expected_type = self.config_attr[conf_param]['expected_type']
                value = self.config_values[conf_param]

                is_valid = self._is_valid_type(conf_param,expected_type,value)
                if not is_valid:
                    invalid_items[conf_param] = {
                        'type': type(self.config_values[conf_param]),
                        'expected_type': expected_type,
                        'value': value
                    }
        # Check extra parameters
        for extra_conf_param in self.extra_attr.keys():
            if extra_conf_param in self.config_values.keys():
                expected_type = self.extra_attr[extra_conf_param]['expected_type']
                value = self.config_values[extra_conf_param]

                is_valid = self._is_valid_type(extra_conf_param,expected_type,value)

                if not is_valid:
                    invalid_items[extra_conf_param] = {
                        'type': type(self.config_values[extra_conf_param]),
                        'expected_type': expected_type,
                        'value': value
                    }

        # Invalid items
        if invalid_items or missing_items:
            if missing_items:
                for conf_param in missing_items:
                    print(f"  ERROR: Configuration missing for '{conf_param}' in the config file")
            if invalid_items:
                for conf_param in invalid_items.keys():
                    print(f"  ERROR: Configuration for '{conf_param}': format unexpected ({invalid_items[conf_param]['type']} instead of {invalid_items[conf_param]['expected_type']}) => '{invalid_items[conf_param]['value']}'")
            exit(1)
        else:
            print("  >> Configuration parameters look OK")


    def _is_valid_type(self, conf_param:str, expected_type:str, value) -> bool:
        '''
        Check the item value is in the valid type.

        Parameters
        ----------
        conf_param : [str] Name of the configuration parameter (e.g. db_name)
        expected_type: [str] Name of the expected data type (e.g. string)
        value: Value of the configuration parameter
        '''
        is_valid = True
        match expected_type:
            case 'string':
                if not isinstance(value, str):
                    is_valid = False
            case 'numeric':
                if not value.isnumeric():
                    is_valid = False
            case 'path':
                if not os.path.exists(value):
                    if not os.path.exists(os.path.join(os.getcwd(),value)):
                        is_valid = False
            case 'date (YYYY-MM-DD)':
                if not re.match('^\d{4}-\d{2}-\d{2}$',value):
                    is_valid = False
            case _:
                print(f"  The attribute {conf_param} expected type ({expected_type}) is not a recognised type in the config module")
        return is_valid


    def _validate_db_conn(self) -> None :
        """
        Validates that the database exists and is accessible, using the provided "db" parameters.
        """
        try:
            # Connect to an existing database
            conn = psycopg.connect(
                f"""dbname={self.config_values['db_name']}
                user={self.config_values['db_user']}
                password={self.config_values['db_password']}
                host={self.config_values['db_host']}
                port={self.config_values['db_port']}"""
            )
            conn.close()
            print("  >> Database connection parameters look OK")
        except psycopg.OperationalError as err:
            print(f"\n  ERROR: Problem connecting to the database {self.config_values['db_name']}: {err}")
            exit(1)


    def _get_db_password(self) -> None:
        '''
        Get database password, if not already supplied.
        '''
        if "db_password" not in self.config_values.keys():
            self.config_values["db_password"] = maskpass.askpass("  Enter database admin user password: > ", mask="")