# Running the scripts

The scripts in these directories can be used to run the entire cycle:

1. Initialise the backend database
2. Run `sacct` command, enhance the data and load it into the databse
3. Set up the dashboards, users, etc.

It should then be possible to view the data in the dashboards running on the Grafana server.

## Backend database set-up
Use `init_db.sh`.

Example:
```
sh scripts/backend/init_db.sh <password>
```
where `<password>` in this case corresponds to the back-end `postgres` user password.

**WARNING!!** This script will delete any existing instance of the database, including all its data, so only run this if you are sure that's what you want.

As well as setting up the database and its tables, the script also adds users to the database; alternatively, you can run the `add_users_to_database.py` script directly. Note that we want to add users to the database before running `sacct`; the users we want should exists in the backend database regardless of whether there is any `sacct` data for them!


## Extract data with `sacct`, and enrich it
Assuming you cannot run the code for the database, etc., on the HPC machine, you will need to run just the `sacct` command
for the desired period.

Example:
```
python run_sacct_only.py -S 2025-04-14 -E 2025-04-15 -a -o sacct_20250414.txt
```
In this case, the script will save the output of the command into a file (on the HPC machine) called `sacct_20250414.txt`; you would then download that file, and add the data into the database, e.g., by using the `add_data_to_db.sh` script, in which case you would need to update the `sacct_file` variable in that script to your path to `sacct_20250414.txt`. Or, you can run the `run_backend.sh` script directly if you prefer (`add_data_to_db.sh` calls this anyway) with the `--useCustomLogs` option set. For example:

```
sh scripts/backend/run_backend.sh \
   --db_name ga_db --db_user postgres --db_password <password> \
   --useOtherInfrastructureInfo ~/repos/GA4HPCdashboard/ga_dashboard/samples \
   --fixed_params_file ~/repos/GA4HPCdashboard/ga_dashboard/data/fixed_parameters.yaml \
   --useCustomLogs path/to/downloaded/file/sacct_20250414.txt 
```
Note that:
* The options for the start and end dates, `-S` and `-E`, are not needed, as the date range will be determined by the contents of the `sacct` output file.
* The directory given with the `--useOtherInfrastructureInfo` option must contain **both** the cluster information file (`cluster_info.yaml`) and the file listing the HPC users (`users_list.csv`); here, the `samples` subdirectory, which is part of the repo, is used.
* In this example, we use the file `sacct_20250414.txt`, which you just generated. Sample `sacct`-output files are also in the `samples` subdirectory. 

Alternatively, if you are able to run everything on the HPC machine, invoke the `run_backend.sh` script WITHOUT the `--useCustomLogs` option. For example:

```
sh scripts/backend/run_backend.sh --db_name ga_db --db_user postgres --db_password <password> 
    -S 2025-04-14 -E 2025-04-15 \
    --useOtherInfrastructureInfo ~/repos/GA4HPCdashboard/ga_dashboard/samples \
    --fixed_params_file ~/repos/GA4HPCdashboard/ga_dashboard/data/fixed_parameters.yaml
```

Obviously, you will need to change the values passed as the script arguments to your own set-up. You will also need the `-S` and `-E` options, as shown above.

## Grafana set-up
A number of things need to be done, assuming you have downloaded Grafana and are able to run its server. These are:
* import the dashboard(s) you want to use into the server
* add users (and their information) to the server

For example:

```
% python scripts/frontend/run_dashboard.py --admin_password <grafana_admin_password> \
       --input_file ga_dashboard/samples/grafana_users_list.csv \
       --db_name ga_db --db_user postgres --db_password <db_password> \
       --input_dir ga_dashboard/dashboards    <-- If not set, uses default dashboard .json directory.
       --name grafana-postgresql-datasource   <-- If not set, uses "grafana-postgresql-ga_db" 
```

**NOTE:** The `--name` argument refers to the name of the datasource you want to use, i.e, it will create a data source (Postgres database) and give it the name you specify. This name must be the same name used in your dashboard JSON file(s). This name must correspond to the `label` field in the JSON files; it will probably be at or near the top of each JSON file. For example:

```
{
  "__inputs": [
    {
      "name": "DS_GRAFANA-POSTGRESQL-GA_DB",
      "label": "grafana-postgresql-ga_db",
      "description": "",
      "type": "datasource",
      "pluginId": "grafana-postgresql-datasource",
      "pluginName": "PostgreSQL"
    }
  ],
  ...
  ```

To use this dashboard, you would need to use the option `--name grafana-postgresql-ga_db` with `run_dashboard.py` (as in the example above).

[Back to Contents](../docs/Contents.md)
