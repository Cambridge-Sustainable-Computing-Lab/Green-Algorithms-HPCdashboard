#!/bin/bash

# To use:
# sh scripts/end-to-end/demo.sh <your_password>
# assuming your password for the backend database user (postgres) is "your_password" 

# set -x # Uncomment this to echo commands to screen (for debugging)

# Abort script if we encounter any errors:
set -e  # Although, see https://stackoverflow.com/questions/39773637/in-a-bash-script-test-error-code-from-a-called-script

echo "\n\n ******* Demo script started. *******\n" 

db_password="$1"      # Gets your Postgres database user password from the command line.
grafana_password="$2" # Gets your Grafana admin password from the command line.

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
# Config file. Change as required.
#
###############################################################
config_file="$repo_root_dir/configuration/examples/config__demo.txt"


###############################################################
#
# Scripts
#
###############################################################

echo "\n*** Setup Grafana: ***\n" # This step will fail if Grafana is not running.
python $repo_root_dir/scripts/install_GAdashboard.py --config $config_file --db_pass $db_password --grafana_pass $grafana_password
echo "\n* Done! *\n"

echo "\n*** Imnport log data: ***\n"
python $repo_root_dir/scripts/run_green_algorithms_on_historical_logs.py --config $config_file --db_pass $db_password
echo "\n* Done! *\n"

echo "\n ******* Demo script completed. *******\n\n" 
