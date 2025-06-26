

# Script to create a more user-friendly interface to the other scripts.

# Place your values in the user section.

class Runner:

    def __init__(self):
        #self.initialise_strings()
        self.create_client_lists()
        self.create_defaults_dict()
        

    def create_client_lists(self):
        files = {}

        # List of all client scripts in scripts/frontend:
        files["frontend"] = [ "test" ]

        # List of all client scripts in scripts/database: 
        files["database"] = [ "add_users_to_database.py", "create_or_overwrite_database.sh", "import_mockup_aggregate.py" ]

        # List of all client scripts inscripts/backend:
        files["backend"] = []

        # Now populate "mydir" dictionary. e.g. mydir["add_users_to_database.py"] = "database"
        # res = [[i for i in test_dict[x]] for x in test_dict.keys()]
        mydir = {}
        for directory in files.keys():
            for client in files[directory]:
                mydir[client] = directory 
        print(mydir)
        self.mydir = mydir


    def create_defaults_dict(self):
        '''
        Create "defaults" dictionary. Key = argument name, value = default value
        '''
        defaults = {}
        defaults["db_name"] = "ga_db"  # The name of the database to store your raw and enriched `sacct` data
        defaults["db_user"] = "postgres" # The default database user

    def create_clients_dict(self):
        '''
        Create "clients" dictionary.
        Key = argument name. Value = list of the scripts (clients) which can use this argument.
        
        '''
        clients = {} # NB what to do where there is both a .sh and .py file? e.g. run_backend.sh
        clients["db_name"] = [ "backend/run_backend.py", "database/add_users_to_database.py" ]

    #def initialise_strings(self):


if __name__ == "__main__":
    runner = Runner()
    