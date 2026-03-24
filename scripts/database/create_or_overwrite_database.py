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

def database_exists(db_name, db_host, db_port, db_user):
    """Return True if a PostgreSQL database with db_name already exists."""
    result = subprocess.run(
        [
            "psql",
            "-U", db_user,
            "-h", db_host,
            "-p", db_port,
            "-tAc",
            f"SELECT 1 FROM pg_database WHERE datname='{db_name}';",
        ],
        capture_output=True,
        text=True,
    )
    # psql outputs "1" when the database is found
    return result.stdout.strip() == "1"

def main():

    argparser = argparse.ArgumentParser(description="Create or overwrite the PostgreSQL database.")

    argparser.add_argument("--db_name",help='Name of database to create or overwrite', required=False, metavar='DB_NAME', default="ga_db", dest='db_name')
    argparser.add_argument("--db_host", help='Name or IP address of host running the database', required=False, metavar='HOST', default='localhost', dest='db_host')
    argparser.add_argument("--db_port", help='Port of host running the database', required=False, metavar='PORT', default='5432', dest='db_port')
    argparser.add_argument("--db_user", help='Name of database admin user', required=False, metavar='DB_USER', default='postgres', dest='db_user')
    argparser.add_argument("--db_password", help='Password of database admin user', required=True, metavar='DB_PASS', dest='db_password')
    argparser.add_argument("--db_script", help='Path to database setup script', required=False, metavar='DB_SCRIPT', default='ga_dashboard/database/ga_db.sql', dest='db_script')
    argparser.add_argument("--skip_db_overwrite", help='Skip drop/recreate if the database already exists', required=False, metavar='SKIP_DB_OVERWRITE', default='False', dest='skip_db_overwrite')
    # argparser.add_argument("--pg_version", help='Version of PostgreSQL being used', required=False, metavar='PG_VERSION', default='13', dest='pg_version')

    #argparser.add_argument("--debug", "-d", help='Debug mode', required=False, dest='debug', action='store_true')

    args = argparser.parse_args()

    db_name = args.db_name
    db_host = args.db_host
    db_port = args.db_port
    db_user = args.db_user
    db_password = args.db_password
    db_script = args.db_script
    skip_db_overwrite = args.skip_db_overwrite

    #debug = args.debug

    #logging_level = logging.DEBUG if debug else logging.INFO
    #logging.basicConfig(format='%(levelname)s: %(message)s', level=logging_level)

    print("\n ******* create_or_overwrite_database script started. *******\n" )

    # Check if we have psql on our PATH
    try:
        _ = subprocess.check_output("which psql", stderr=subprocess.STDOUT, shell = True)
    except subprocess.CalledProcessError:
        print("\nI could not find the `psql` program on your PATH.\nGoodbye.\n")
        sys.exit(1)

    # We temporarily use an environment variable to store the database admin password.
    # The following are the commands issued, in a format which is easier to read!
    # export PGPASSWORD="$db_password"
    os.environ['PGPASSWORD'] = f"{db_password}"

    db_found = database_exists(db_name, db_host, db_port, db_user)
    if db_found:
        print(f"\n[Info] Database '{db_name}' was found on {db_host}:{db_port}.")
        if skip_db_overwrite.lower() == 'true':
            print(
                f"[Info] 'skip_if_exists' is enabled in the configuration.\n"
                f"       Skipping drop/recreate of '{db_name}'. Nothing was changed.\n"
            )
            os.environ["PGPASSWORD"] = ""
            print(" ******* create_or_overwrite_database script completed (skipped). *******\n")
            sys.exit(0)
        else:
            print("\n*** Setting up empty Postgres database: ***\n")
            print("NB Have you configured the values you want in this script?")    
            print("\n** Use CTRL-C to stop script. **")

            # Make user confirm this potentially drastic action!
            print(f"\nWARNING! This will delete database '{db_name}'! Are you sure you wish to continue?")
            answer = input("Type YES to continue, else script will abort. > ")
            print()
            if answer not in ["YES","yes"]:
                sys.exit(2)                                               

            # delete existing db, create new, and set it up
            # psql -c 'drop database if exists ga_db; ' -U postgres -h $db_host -p $db_port
            # psql -c 'create database ga_db; ' -U postgres -h $db_host -p $db_port
            # psql -U $db_user -h $db_host -p $db_port -d ga_db < $repo_root_dir/ga_dashboard/database/ga_db.sql
            subprocess.run(["psql", "-c", f"drop database if exists {db_name}; ", "-U", f"{db_user}", "-h", f"{db_host}", "-p", f"{db_port}"])
            subprocess.run(["psql", "-c", f"create database {db_name}; ", "-U", f"{db_user}", "-h", f"{db_host}", "-p", f"{db_port}"])
            subprocess.run(["psql", "-U",  f"{db_user}", "-h", f"{db_host}", "-p", f"{db_port}", "-d", f"{db_name}", "-f", f"{db_script}"])
    else:
        # only create and setup db
        # psql -c 'create database ga_db; ' -U postgres -h $db_host -p $db_port
        # psql -U $db_user -h $db_host -p $db_port -d ga_db < $repo_root_dir/ga_dashboard/database/ga_db.sql
        subprocess.run(["psql", "-c", f"create database {db_name}; ", "-U", f"{db_user}", "-h", f"{db_host}", "-p", f"{db_port}"])
        subprocess.run(["psql", "-U",  f"{db_user}", "-h", f"{db_host}", "-p", f"{db_port}", "-d", f"{db_name}", "-f", f"{db_script}"])
    
    # Resets back to nothing
    os.environ['PGPASSWORD'] = ""
    print("\n ******* create_or_overwrite_database script completed. *******\n")

if __name__ == "__main__":
     main()
