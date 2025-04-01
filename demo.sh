#!/bin/bash

# To use:
# sh ./demo.sh your_password
# assuming your password for the backend database user (postgres) is "your_password" 

# set -x # Uncomment this to echo commands to screen (for debugging)

# Abort script if we encounter any errors:
set -e  # Although, see https://stackoverflow.com/questions/39773637/in-a-bash-script-test-error-code-from-a-called-script

echo "\n\n ******* Demo script started. *******\n" 

db_password="$@" # Gets your password from the command line.

# Change the values in "Your values" section (further down) as required.

repo_root_dir="$(pwd)"
echo "current dir is $repo_root_dir" # Probably ..../GA4HPCdashboard

###############################################################
#
# Default values
#
###############################################################
DEFAULT_GRAFANA_USER="admin"
DEFAULT_GRAFANA_ADMIN_PASSWORD="admin" 
DEFAULT_GRAFANA_DASHBOARD_FOLDER_NAME="Green Algorithms Demo"
DEFAULT_GRAFANA_DASHBOARDS_DIR=$repo_root_dir ### $repo_root_dir/frontend/dashboards/prod" 
DEFAULT_GRAFANA_URL="localhost:3000"
DEFAULT_DB_NAME="ga_db"
DEFAULT_DB_HOST="localhost"
DEFAULT_DB_PORT=5432
DEFAULT_DB_USER="postgres"
DEFAULT_START_DATE="2025-02-14"
DEFAULT_END_DATE="2025-02-18"
DEFAULT_INFRASTRUCTURE_DIR="$repo_root_dir/ga_dashboard/samples"
DEFAULT_DATASOURCE_NAME="demo_datasource"  # "grafana-postgresql-ga_db" 
DEFAULT_POSTGRES_VERSION=13
DEFAULT_USERS_FILE="$repo_root_dir/ga_dashboard/samples/common_users_list.csv"
DEFAULT_SACCT_FILE="$repo_root_dir/ga_dashboard/samples/sacct_output_single_user.txt"

###############################################################
#
# Your values. Change as required.
#
###############################################################
grafana_admin_user=$DEFAULT_GRAFANA_USER
grafana_admin_password=$DEFAULT_GRAFANA_ADMIN_PASSWORD  # You should probably change this!
grafana_dashboard_folder_name=$DEFAULT_GRAFANA_DASHBOARD_FOLDER_NAME
grafana_dashboard_directory=$DEFAULT_GRAFANA_DASHBOARDS_DIR
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
datasource_name=$DEFAULT_DATASOURCE_NAME
grafana_url=$DEFAULT_GRAFANA_URL
common_users_file=$DEFAULT_USERS_FILE
sacct_file=$DEFAULT_SACCT_FILE

echo "\n*** Importing users to Grafana: ***\n" # This step will fail if Grafana is not running.
python $repo_root_dir/frontend/import_users.py --input_file $common_users_file \
    --admin_login $grafana_admin_user --admin_password $grafana_admin_password \
    --dashboard_folder "$grafana_dashboard_folder_name"   # --debug
echo "\n* Done! *\n"

echo "\n*** Importing users to backend database: ***\n"
python $repo_root_dir/ga_dashboard/add_users_to_database.py --db_name $db_name \
    --db_user $db_user --db_password $db_password --db_port $db_port --db_host $db_host \
    --input_file $common_users_file
echo "\n* Done! *\n"

echo "\n*** Transforming user data (from sacct command output) and inserting to backend database: ***\n"
sh $repo_root_dir/ga_dashboard/run_backend.sh --db_name $db_name --db_user $db_user --db_password $db_password  \
    -S $start_date -E $end_date --useOtherInfrastructureInfo $infrastructure_dir --useCustomLogs $sacct_file
    # Optional: --reportBug --reportBugHere --useCustomLogs
echo "\n* Done! *\n"

echo "\n*** Adding the data source (backend database) into Grafana: ***\n"
python $repo_root_dir/frontend/create_data_source.py --name $datasource_name \
    --admin_login $grafana_admin_user --admin_password $grafana_admin_password \
    --db_name $db_name --db_user $db_user --db_password $db_password --db_host $db_host --db_port $db_port \
    --pg_version $pg_version --url $grafana_url      --debug
echo "\n* Done! *\n"

echo "\n*** Importing the demo dashboard into Grafana: ***\n"
# --input_dir is the directory where the dashboard JSON files you want to import are located (e.g. the default value I put script_path+'/dashboards/prod/')
#  --dashboard_folder_name is the name you want to use for the Grafana folder (e.g. the default value I put: Green Algorithms)
python $repo_root_dir/frontend/import_dashboards.py --input_dir $grafana_dashboard_directory --url $grafana_url  \
    --admin_login $grafana_admin_user --admin_password $grafana_admin_password \
    --dashboard_folder_name "$grafana_dashboard_folder_name"  --debug
exit

echo "\n ******* Demo script completed. *******\n\n" 
