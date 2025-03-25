import os, argparse, csv
import logging
import psycopg

logger = logging.getLogger(__name__)

"""
Script to add users in a file to the ga_user table in Postgres.

Example: 
python add_users_to_database.py --db_name ga_db --db_user postgres --db_password mypassword --db_port 5432 --db_host localhost
        --input_file samples/common_users_list.csv

TODO I want to move this into a proper database wrapper class, which is used for all interaction with Postgres. It would be
database-agnostic:

DB = Database(...)
DB.connect()
DB.add_users()
DB.disconnect()

So it can be changed from postgres if desired.
"""

class User:
    ''' Represent a user to be added to the ga_user table in the database. '''

    def __init__(self, data:dict) -> None:
        #base_url = "http://{}:{}@{}".format(login, password, grafana_url)
        # self.grafana = GrafanaApi.from_url(base_url)
        # self.check_grafana_is_on()
        if not data:
            logger.error("User constructor: no data!")
            exit(1)

        count = 0

        if "User" in data:
            self.user = data["User"]
            count += 1

        if "UID" in data:
            self.uid = data["UID"]
            count += 1

        if "Name" in data:
            self.name = data["Name"]
            count += 1

        if "Group" in data:
            self.group = data["Group"]
            count += 1
        elif "Team name" in data:
            self.group = data["Team name"]
            count += 1

        if "Department" in data:
            self.dept = data["Department"]
            count += 1

        if count != 5:
            logger.error("User constructor: error in data. Dict: " + str(data))
            exit(1)  

    def to_tuple(self) -> tuple:
        """
        Return the object's member values as a tuple.
        """
        return self.user, self.uid, self.name, self.group, self.dept


def build_command_string(user_objects: list) -> str:
    """
    Generate the SQL command string to send to the database.

    Args:
        user_objects (list): List of User objects.

    Returns:
        str: The command.
    """
    command = "INSERT INTO ga_user (user_name, uid, name, group_name, department) VALUES "
    more_than_one = False; # Handle commas if more than one row to add to database.
    for uobj in user_objects:
        if more_than_one:
            command += ','
        uobj_str = f"({uobj.user}, {uobj.uid}, {uobj.name}, {uobj.group}, {uobj.dept})"
        command += uobj_str
        more_than_one = True 
    return command


def build_data_to_execute(user_objects: list) ->list:
    """
    Generate list of data to send to the SQL execute command.
    Doing it this way, rather than building a string, to avoid SQL injection

    Args:
        user_objects (list): List of User objects.

    Returns:
        list: The list of value sets to send to the execute command.
    """
    mylist = []
    for uobj in user_objects:
        mylist.append(uobj.to_tuple)
    return mylist


def create_arguments():
    """
    Command line arguments for the script.
    :return: argparse object
    """
    parser = argparse.ArgumentParser(description=f'Add/update users to ga_user table in database.')
   
    # Required settings for the user data to be imported into a database
    parser.add_argument('--db_name', type=str, required=True, help='Database name')
    parser.add_argument('--db_user', type=str, required=True, help='Database user name')
    parser.add_argument('--db_password', type=str, required=True, help='Database user password')
    parser.add_argument('--db_port', type=int, required=True, help='Database port', default=5432)
    parser.add_argument('--db_host', type=str, required=True, help='Database server host', default='localhost')
    parser.add_argument('--input_file', type=str, required=True, help='CSV file of user data')

    args = parser.parse_args()

    input_file = args.input_file
    if not os.path.isfile(input_file):
        logger.error("File '" + input_file + "' can't be found")
        exit(1)

    return args


def parse_file(input_file: str) -> list:
    """ 
    Extracts user data from the CSV file. Returns it as a list of User objects 

    Args:
        input_file (str: Path to input CSV file.

    Returns:
        list: The list of User objects.
    """
    
    users = []

    with open(input_file, newline='') as csvfile:
    
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        for row in reader:
            user = User(row)
            users.append(user)

    return users


if __name__ == "__main__":

    logging_level = logging.DEBUG
    
    args = create_arguments()
    user_objects = parse_file(args.input_file)
    
    # TODO: move to a Database class
    try:
        conn = psycopg.connect(
            dbname=args.db_name,
            user=args.db_user,
            password=args.db_password,
            host=args.db_host,
            port=args.db_port
        )
    except psycopg.OperationalError as err:
        logger.error("Unable to connect to database: {err}")
        exit(1)
    
    cur = conn.cursor()

   # sql = build_command_string(user_objects)

    # data_to_execute = build_data_to_execute(user_objects)
    sql = "INSERT INTO ga_user (user_name, uid, name, group_name, department) VALUES (%s, %s, %s, %s, %s)"

    for uobj in user_objects:
        data = uobj.to_tuple()
        cur.execute(sql, data)

    # Make the changes to the database persistent
    conn.commit()
 
    # Close communication with the database
    cur.close()
    conn.close()

    print ("Script completed successfully.")
