#!/bin/bash
#
# Gets the data from the sacct command and adds it to the back-end database.
#
# Run from the top-level directory of the repo. To use:
#
# sh scripts/backend/add_data_to_db.sh your_password
#
# assuming your password for the backend database user (postgres) is "your_password" 
#
# This script assumes that the database has been created and the relevant users added;
# this can be done by running the init_db.script (q.v.).

# set -x # Uncomment this to echo commands to screen (for debugging)

# Abort script if we encounter any errors:
#set -e  # Although, see https://stackoverflow.com/questions/39773637/in-a-bash-script-test-error-code-from-a-called-script

echo "\n\n ******* add_data_to_db script started. *******\n" 

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
#DEFAULT_START_DATE="2025-02-14"
#DEFAULT_END_DATE="2025-02-18"
DEFAULT_INFRASTRUCTURE_DIR="$repo_root_dir/ga_dashboard/samples"
DEFAULT_POSTGRES_VERSION=13
DEFAULT_USERS_FILE="$repo_root_dir/ga_dashboard/samples/users_list.csv"
DEFAULT_SACCT_FILE="$repo_root_dir/ga_dashboard/samples/sacct_output_single_user.txt"
DEFAULT_FIXED_PARAMETERS_FILE="$repo_root_dir/ga_dashboard/data/fixed_parameters.yaml"

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
start_date=$DEFAULT_START_DATE
end_date=$DEFAULT_END_DATE
infrastructure_dir=$DEFAULT_INFRASTRUCTURE_DIR
# --reportBug for run_backend.sh
# --reportBugHere for run_backend.sh
# --useCustomLogs for run_backend.sh
sacct_file=$DEFAULT_SACCT_FILE
fixed_params_file=$DEFAULT_FIXED_PARAMETERS_FILE

#echo "\n*** Setting up Postgres database: ***\n"
#export PGPASSWORD="$db_password"
#psql -c 'drop database if exists ga_db; ' -U postgres -h $db_host -p $db_port
#psql -c 'create database ga_db; ' -U postgres -h $db_host -p $db_port
#psql -U $db_user -h $db_host -p $db_port -d ga_db < $repo_root_dir/ga_dashboard/database/ga_db.sql
#export PGPASSWORD=
#echo "\n* Done! *\n"



echo "\n*** Transforming user data (from sacct command output) and inserting to backend database: ***\n"
sh $repo_root_dir/scripts/backend/run_backend.sh --db_name $db_name --db_user $db_user --db_password $db_password  \
    --useOtherInfrastructureInfo $infrastructure_dir --useCustomLogs $sacct_file \
    --fixed_params_file $fixed_params_file

    # Optional: --reportBug --reportBugHere --useCustomLogs
echo "\n* Done! *\n"





echo "\n ******* add_data_to_db script completed. *******\n\n" 
