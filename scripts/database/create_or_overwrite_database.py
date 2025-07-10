# Script which initialises the back-end database. Default name: ga_db
#
# It does not add any data to the database, just the tables.
#
# Run from top-level directory. To use:
#
# python scripts/backend/create_or_overwrite_database.py
#
# This will give you a chance to cancel it if you invoked this script by mistake.    

import argparse
import os
import subprocess
import sys

# If you get an error like this:
#     ERROR:  database "ga_db" is being accessed by other users
#     DETAIL:  There is 1 other session using the database.
# you may need to restart the Grafana server, as it connects to Postgres.

def main():

    argparser = argparse.ArgumentParser(description="Create or overwrite the PostgreSQL database.")

    argparser.add_argument("--db_name",help='Name of database to create or overwrite', required=False, metavar='DB_NAME', default="ga_db", dest='db_name')
    argparser.add_argument("--db_host", help='Name or IP address of host running the database', required=False, metavar='HOST', default='localhost', dest='db_host')
    argparser.add_argument("--db_port", help='Port of host running the database', required=False, metavar='PORT', default='5432', dest='db_port')
    argparser.add_argument("--db_user", help='Name of database admin user', required=False, metavar='DB_USER', default='postgres', dest='db_user')
    argparser.add_argument("--db_password", help='Password of database admin user', required=True, metavar='DB_PASS', dest='db_password')
    argparser.add_argument("--db_script", help='Path to database setup script', required=False, metavar='DB_SCRIPT', default='ga_dashboard/database/ga_db.sql', dest='db_script')
    # argparser.add_argument("--pg_version", help='Version of PostgreSQL being used', required=False, metavar='PG_VERSION', default='13', dest='pg_version')

    #argparser.add_argument("--debug", "-d", help='Debug mode', required=False, dest='debug', action='store_true')

    args = argparser.parse_args()

    db_name = args.db_name
    db_host = args.db_host
    db_port = args.db_port
    db_user = args.db_user
    db_password = args.db_password
    db_script = args.db_script

    #debug = args.debug

    #logging_level = logging.DEBUG if debug else logging.INFO
    #logging.basicConfig(format='%(levelname)s: %(message)s', level=logging_level)

    print("\n\n ******* create_or_overwrite_database script started. *******\n" )

    # Check if we have psql on our PATH
    try:
        _ = subprocess.check_output("which psql", stderr=subprocess.STDOUT, shell = True)
    except subprocess.CalledProcessError:
        print("\nI could not find the `psql` program on your PATH.\nGoodbye.\n")
        sys.exit(1)

    print("\n*** Setting up empty Postgres database: ***\n")
    print("NB Have you configured the values you want in this script?")    
    print("\n** WARNING: this will delete any existing data in the database. **\n")
    print("\n** Use CTRL-C to stop script. **\n")

    # Make user confirm this potentially drastic action!
    print(f"\nWARNING! This will delete database '{db_name}' (if it exists)! Are you sure you wish to continue?")
    answer = input("Type YES to continue, else script will abort. > ")
    print()
    if answer != "YES":
        sys.exit(2)                                               

    # We temporarily use an environment variable to store the database admin password.
    os.environ['PGPASSWORD'] = f"{db_password}"
    subprocess.run(["psql", "-c", f"drop database if exists {db_name}; ", "-U", f"{db_user}", "-h", f"{db_host}", "-p", f"{db_port}"])
    subprocess.run(["psql", "-c", f"create database {db_name}; ", "-U", f"{db_user}", "-h", f"{db_host}", "-p", f"{db_port}"])
    subprocess.run(["psql", "-U",  f"{db_user}", "-h", f"{db_host}", "-p", f"{db_port}", "-d", f"{db_name}", "-f", f"{db_script}"])
    os.environ['PGPASSWORD'] = ""

    print("\n ******* create_or_overwrite_database script completed. *******\n\n")

if __name__ == "__main__":
     main()
