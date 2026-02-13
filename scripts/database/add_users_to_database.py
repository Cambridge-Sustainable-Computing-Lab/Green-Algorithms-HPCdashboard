import argparse 
import csv
import logging
import os
from datetime import datetime, timezone

from ga_dashboard.backend.services.database_service import DBSettings, DatabaseService
from ga_dashboard.database.table_col_definitions import GA_USER_COLUMNS

logger = logging.getLogger(__name__)

"""
Script to add users in a file to the ga_user table in Postgres.

Example: 
python scripts/database/add_users_to_database.py --db_name ga_db --db_user postgres --db_password mypassword 
        --db_port 5432 --db_host localhost --dashboard_users_file configuration/examples/user_list__demo.csv

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
        IMPORTANT: in same order as the INSERT command used!
        """
        return self.user, self.uid, self.name, self.group, self.dept


def create_arguments():
    """
    Command line arguments for the script.
    :return: argparse object
    """
    parser = argparse.ArgumentParser(description='Add/update users to ga_user table in database.')
   
    # Required settings for the user data to be imported into a database
    parser.add_argument('--db_name', type=str, required=True, help='Database name')
    parser.add_argument('--db_user', type=str, required=True, help='Database user name')
    parser.add_argument('--db_password', type=str, required=True, help='Database user password')
    parser.add_argument('--db_port', type=int, required=True, help='Database port', default=5432)
    parser.add_argument('--db_host', type=str, required=True, help='Database server host', default='localhost')
    parser.add_argument('--dashboard_users_file', type=str, required=True, help='Dashboard users datafile (CSV format)')

    args = parser.parse_args()

    input_file = args.dashboard_users_file
    if not os.path.isfile(input_file):
        logger.error("File '" + input_file + "' can't be found")
        exit(1)

    return args


def parse_file(input_file: str) -> list:
    """ 
    Extracts user data from the CSV file. Returns it as a list of User objects 

    Args:
        input_file (str): Path to input CSV file.

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
    user_objects = parse_file(args.dashboard_users_file)

    db_settings = DBSettings(
        db_name=args.db_name,
        user=args.db_user,
        password=args.db_password,
        host=args.db_host,
        port=args.db_port,
    )

    # Prepare rows as list[dict]
    rows = []

    for uobj in user_objects:
        values = uobj.to_tuple()
        row_dict = dict(zip(GA_USER_COLUMNS[:-1], values))
        row_dict["updated"] = datetime.now(timezone.utc)
        rows.append(row_dict)

    print('> DB insertion into ga_user - start')

    with DatabaseService(db_settings) as db:
        if not db._conn or db._conn.closed:
            print('DB connection error')
            exit(1)

        db.insert_data(
            table_name="ga_user",
            columns=GA_USER_COLUMNS,
            rows=rows,
            on_conflict="DO UPDATE",
            conflict_target=["user_name"],
            update_columns=GA_USER_COLUMNS[1:],  # skips user_name, updates everything else including updated
        )

    print('> DB insertion into ga_user - end')
    print("Script completed successfully.")



