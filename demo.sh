#!/bin/bash

# To use:
# sh ./demo.sh your_password
# assuming your password for the backend database user (postgres) is "your_password" 

echo "\n\n ******* Demo script started. *******\n" 

mypassword="$@" # Gets your password from the command line.

# set -x # Uncomment this to echo commands to screen (for debugging)

# Abort script if we encounter any errors:
set -e  # Although, see https://stackoverflow.com/questions/39773637/in-a-bash-script-test-error-code-from-a-called-script

userCWD="$(pwd)"
echo "current dir is $userCWD" # Probably ..../GA4HPCdashboard

common_users_file="$userCWD/ga_dashboard/samples/common_users_list.csv"

echo "\n*** Importing users to Grafana: ***\n" # NB check Grafana is running first

python frontend/import_users.py --input_file $userCWD/ga_dashboard/samples/grafana_users_list.csv --admin_login admin --admin_password admin
echo "\n* Done! *\n"

echo "\n*** Importing users to backend database: ***\n"
python ga_dashboard/add_users_to_database.py --db_name ga_db --db_user postgres --db_password "$mypassword" --db_port 5432 --db_host localhost \
        --input_file $userCWD/ga_dashboard/samples/common_users_list.csv
echo "\n* Done! *\n"

echo "\n*** Transforming user data (from sacct command output) and inserting to backend database: ***\n"
sh $userCWD/ga_dashboard/run_backend.sh --db_name ga_db --db_user postgres --db_password $mypassword -S 2025-02-14 -E 2025-02-18 \
    --useOtherInfrastructureInfo samples --useCustomLogs samples/sacct_output_single_user.txt
echo "\n* Done! *\n"


echo "\n\n ******* Demo script completed. *******\n\n" 
