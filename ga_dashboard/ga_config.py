import os
import re
import maskpass
import psycopg
import yaml


class GAConfig:
    # Class to parse, store and validate the configuration data into a dictionary

    # Mandatory parameters
    config_attr = {
        'admin_login': { 'expected_type': 'string' },
        'cluster_info_file': { 'expected_type': 'path' },
        'dashboard_folder_name': { 'expected_type': 'string' },
        'dashboard_users_file': { 'expected_type': 'path' },
        'db_host': { 'expected_type': 'string' },
        'db_name': { 'expected_type': 'string' },
        'db_port': { 'expected_type': 'numeric' },
        'db_script': { 'expected_type': 'string' },
        'db_user': { 'expected_type': 'string' },
        'fixed_params_file': { 'expected_type': 'path' },
        'input_dir': { 'expected_type': 'path' },
        'name': { 'expected_type': 'string' },
        'pg_version': { 'expected_type': 'numeric' },
        'url': { 'expected_type': 'string' }
    }

    # Optional parameters
    extra_attr = {
        'startDay': { 'expected_type': 'date (YYYY-MM-DD)' },
        'endDay': { 'expected_type': 'date (YYYY-MM-DD)' },
        'outFile': { 'expected_type': 'string' },
        'useCustomLogs': { 'expected_type': 'path' },
        'skip_db_overwrite': { 'expected_type': 'boolean'}
    }

    # List of parameters that can't be used together
    exclusion_attr = [
        ['outFile', 'useCustomLogs']
    ]


    def __init__(self, config_file:str, db_pass:str=None, grafana_pass:str=None):
        self.config_file = config_file
        # Default value
        self.config_values = {
            'debug': False
        }
        if db_pass:
            self.config_values['db_password'] = db_pass
        if grafana_pass:
            self.config_values['admin_password'] = grafana_pass


    def ingest_config_file(self,skip_passwords:bool=None) -> None:
        '''
        Parse the config file and obtain any parameter values.

        Parameters
        ----------
        config_file : str. Name of the config file to use.
        '''

        with open(self.config_file, "r") as infile:
            if self.config_file.endswith('.txt'):
                print("ERROR: TXT config files are not supported, please convert to YAML format. Find template in `configuration/templates/config.yaml`")
                exit(1)
            data = yaml.safe_load(infile)

        if not isinstance(data, dict):
            print("ERROR: YAML config must define a mapping at top level")
            exit(1)

        # Merge YAML values into config_values
        for key, value in data.items():
            self.config_values[key] = value

        # Add database password
        if not skip_passwords:
            self._get_db_password()
        # Check values
        self._check_config_values()
        # Check DB connection
        if not skip_passwords:
            self._validate_db_conn()


    def _isSubset(self, main_array:list, sub_array:list) -> bool:

        # Check that each element of sub_array is in main_array
        for item in sub_array:
            if item not in main_array:
                return False

        # If all elements of sub_array are found in the main_array
        return True


    def _check_config_values(self) -> None:
        '''
        Check the configuration parameters.
        '''
        user_config_items = self.config_values.keys()
        invalid_items = {}
        missing_items = []

        # Check for incompatible parameters
        for attrs in self.exclusion_attr:
            if self._isSubset(user_config_items,attrs):
                print(f"  ERROR: the parameters `{'` and `'.join(attrs)}` can't be both set in the config file: only one of them is allowed.")
                exit(1)

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
                is_valid = isinstance(value, str)
            case 'numeric':
                is_valid = isinstance(value, int)
            case 'path':
                if not isinstance(value, str):
                    is_valid = False
                else:
                    if not os.path.exists(value):
                        if not os.path.exists(os.path.join(os.getcwd(), value)):
                            is_valid = False
            case 'date (YYYY-MM-DD)':
                if not isinstance(value, str):
                    is_valid = False
                else:
                    if not re.match(r'^\d{4}-\d{2}-\d{2}$', value):
                        is_valid = False
            case 'boolean':
                is_valid = isinstance(value, bool)
            case _:
                print(f"  The attribute {conf_param} expected type ({expected_type}) is not a recognised type in the config module")
                is_valid = False
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
            print(f"\n  WARNING: Problem connecting to the database {self.config_values['db_name']}: either the database doesn't exist yet or the script can't access the database")
            if 'debug' in self.config_values.keys():
                if self.config_values['debug']:
                    print(f"\n  ERROR message: {err}")


    def _get_db_password(self) -> None:
        '''
        Get database password, if not already supplied.
        '''
        if "db_password" not in self.config_values.keys():
            self.config_values["db_password"] = maskpass.askpass("  Enter database admin user password: > ", mask="")
            