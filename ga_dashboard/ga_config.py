
class GAConfig:
    # Class to parse and store the configuration data into a dictionary
    # TODO:
    # - Improve validation (use groups to be used like in backend/utils/validate_args ?)
    # - Set additional config_attr for the backend script

    # Mandatory parameters
    config_attr = {
        'admin_login': { 'expected_type': str },
        'cluster_info_file': { 'expected_type': str },
        'dashboard_folder_name': { 'expected_type': str },
        'db_host': { 'expected_type': str },
        'db_name': { 'expected_type': str },
        'db_port': { 'expected_type': str },
        'db_script': { 'expected_type': str },
        'db_user': { 'expected_type': str },
        'fixed_params_file': { 'expected_type': str },
        'grafana_users_file': { 'expected_type': str },
        'hpc_users_file': { 'expected_type': str },
        'input_dir': { 'expected_type': str },
        'name': { 'expected_type': str },
        'outFile': { 'expected_type': str },
        'pg_version': { 'expected_type': str },
        'url': { 'expected_type': str }
    }

    def __init__(self, config_file: str):
        self.config_file = config_file
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
            value = pieces[1].rstrip()  # Remove trailing whitespace e.g. \n
            # print(f"Got: *{arg}* and *{value}*")
            
            self.config_values[arg] = value
        # Check values
        self.check_config_values()


    def check_config_values(self) -> None:
        '''
        Check the configuration parameters.
        TODO: Need to be updated/improved (cf. look at backend/utils/validate_args)
        '''
        user_config_items = self.config_values.keys()
        check_ok = True
        for conf_item in self.config_attr.keys():
            expected_type = self.config_attr[conf_item]['expected_type']
            if conf_item not in user_config_items:
                print(f"ERROR: Configuration missing for '{conf_item}' in the config file")
                check_ok = False
            elif (type(self.config_values[conf_item]) != expected_type):
                print(f"ERROR: Configuration for '{conf_item}': format unexpected ({type(self.config_values[conf_item])} instead of {expected_type})")
                check_ok = False
        if check_ok == False:
            exit(1)
        