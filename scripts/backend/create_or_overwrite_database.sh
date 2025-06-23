#!/bin/bash
#
# Script which initialises the back-end database. Default name: ga_db
#
# It does not add any data to the database.
#
# Run from top-level directory. To use:
#
# sh scripts/backend/create_or_overwrite_database.sh
#
# It will prompt you for your postgres password.
# This will give you a chance to cancel it if you invoked this script by mistake.    

# set -x # Uncomment this to echo commands to screen (for debugging)

# Abort script if we encounter any errors:
#set -e  # Although, see https://stackoverflow.com/questions/39773637/in-a-bash-script-test-error-code-from-a-called-script

echo "\n\n ******* create_or_overwrite_database script started. *******\n" 

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
db_setup_script="$repo_root_dir/ga_dashboard/database/ga_db.sql"

echo "\n*** Setting up empty Postgres database: ***\n"
echo
echo "NB Have you configured the values you want in this script?"
echo
echo "\n** WARNING: this will delete any existing data in the database. **\n"
echo "\n** Use CTRL-C to stop script. **\n"

# Make user confirm this potentially drastic action!
echo
echo "WARNING! This will delete database '$db_name'! Are you sure you wish to continue?"
read -p "Type YES to continue, else script will abort."
echo
if [ "$REPLY" != "YES" ]; then
    exit 
fi

psql -c 'drop database if exists '$db_name'; ' -U postgres -h $db_host -p $db_port
psql -U $db_user -h $db_host -p $db_port -d $db_name < $db_setup_script
echo "\n* Done! *\n"

echo "\n ******* create_or_overwrite_database script completed. *******\n\n" 
