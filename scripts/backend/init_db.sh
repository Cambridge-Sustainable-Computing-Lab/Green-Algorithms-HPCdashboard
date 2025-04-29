#!/bin/bash
#
# Script which initialises the back-end database. Default name: ga_db
# ** NB ** This script first deletes any existing instance of the database. It then recreates it and adds 
# users in the specified file. It does not add any data to the database (except for these users).
#
# Run from top-level directory. To use:
#
# sh scripts/backend/init_db.sh your_password
#
# assuming your password for the backend database user (postgres) is "your_password" 

# set -x # Uncomment this to echo commands to screen (for debugging)

# Abort script if we encounter any errors:
#set -e  # Although, see https://stackoverflow.com/questions/39773637/in-a-bash-script-test-error-code-from-a-called-script

echo "\n\n ******* init_db script started. *******\n" 

db_password="$@" # Gets your Postgres database user password from the command line.

# Change the values in "Your values" section (further down) as required.
#
# If you get an error like this:
#     ERROR:  database "ga_db" is being accessed by other users
#     DETAIL:  There is 1 other session using the database.
# you may need to restart the Grafana server, as it connects to Postgres.

repo_root_dir="$(pwd)"
echo "current dir is $repo_root_dir" # Probably ..../GA4HPCdashboard

###############################################################
#
# Default values
#
###############################################################
DEFAULT_DB_NAME="ga_db"
DEFAULT_DB_HOST="localhost"
DEFAULT_DB_PORT=5432
DEFAULT_DB_USER="postgres"
DEFAULT_POSTGRES_VERSION=13
DEFAULT_USERS_FILE="$repo_root_dir/ga_dashboard/samples/hpc_users_list.csv"

###############################################################
#
# Your values. Change as required.
#
###############################################################
db_name=$DEFAULT_DB_NAME
db_host=$DEFAULT_DB_HOST
db_port=$DEFAULT_DB_PORT
db_user=$DEFAULT_DB_USER
pg_version=$DEFAULT_POSTGRES_VERSION
common_users_file=$DEFAULT_USERS_FILE
db_setup_script="$repo_root_dir/ga_dashboard/database/ga_db.sql"
add_users_script="$repo_root_dir/scripts/backend/add_users_to_database.py"

echo "\n*** Setting up Postgres database: ***\n"
export PGPASSWORD="$db_password"  # Saves it briefly as an environment variable.
psql -c 'drop database if exists '$db_name'; ' -U postgres -h $db_host -p $db_port
psql -c 'create database '$db_name'; ' -U postgres -h $db_host -p $db_port
psql -U $db_user -h $db_host -p $db_port -d $db_name < $db_setup_script
export PGPASSWORD=  # Resets the environment variable.
echo "\n* Done! *\n"

echo "\n*** Importing users to backend database: ***\n"
python $add_users_script --db_name $db_name \
    --db_user $db_user --db_password $db_password --db_port $db_port --db_host $db_host \
    --input_file $common_users_file
echo "\n* Done! *\n"


echo "\n ******* init_db script completed. *******\n\n" 
