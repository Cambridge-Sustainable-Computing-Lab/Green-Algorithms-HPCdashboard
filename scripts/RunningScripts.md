# Running the scripts

The scripts in these directories can be used to run the entire cycle:

1. Initialise the backend database
2. Running the backend (run `sacct` command, enhance the data and load it into the database)
3. Set up the dashboards, users, etc.

It should then be possible to view the data in the dashboards running on the Grafana server.

It is envisaged that the first time the backend is run, the data obtained by `sacct` will be that of all the jobs (that the system still has a record of)
which occurred before the current time (perhaps upto the end of the previous day). These would then be loaded into the database, and viewable with the
dashboard.

It is also envisaged that, after this, the backend process will be run as a daily `cron` job, continually updating the database with details of HPC usage,
perhaps over the previous 24 hours or 7 days, say.

Users will need to be added to the HPC users file before running the backend, as the code currently raises an error if a job is encountered
in the `sacct` output with a User which the backend hasn't been told about.

## Backend database set-up
Use `create_or_overwrite_database.sh`.

Example:
```
sh scripts/backend/create_or_overwrite_database.sh
```
This will create a new database with empty tables. If you run it and the database already exists, it will delete your data, as its name suggests.

You will be prompted for your `postgres`-user password. This gives you the chance to CTRL-C out if you invoked it by mistake.

<ins>**WARNING!! This script will delete any existing instance of the database, including all its data, so only run this if you are sure that's what you want.**</ins>

To add HPC users to this database, use the `add_users_to_database.py` script with your `postgres`-user password. For example:
```
python scripts/backend/add_users_to_database.py \
    --db_name ga_db --db_user postgres  --db_port 5432 --db_host localhost \
    --input_file ga_dashboard/samples/hpc_users_list.csv --db_password <your_password>
```

Note that we want to add HPC users to the database before running `sacct`; the users we want should exists in the backend database regardless of whether there is any `sacct` data for them!


## Extract data with `sacct`, and enrich it
We assume that the usual case is that you are able to run the code/scripts for setting up the database, etc., on the same HPC system where you run the `sacct` command.

If so, invoke the `run_backend.sh` script without the `--useCustomLogs` option. For example:

```
sh scripts/backend/run_backend.sh \
    --db_name ga_db --db_user postgres --db_password <password> 
    -S 2025-04-14 -E 2025-04-15 \
    --useOtherInfrastructureInfo ~/repos/GA4HPCdashboard/ga_dashboard/samples \          # NB absolute file path
    --fixed_params_file ~/repos/GA4HPCdashboard/ga_dashboard/data/fixed_parameters.yaml  # NB absolute file path
```

This will extract usage information using `sacct`, enhance it (work out some additional quantities using it), then add it to the database. Obviously, you will need to change the values passed as the script arguments to your own set-up. You will also need the `-S` and `-E` options, as shown above.


However, assuming you **cannot** run the code/scripts on the HPC system, you will need to run just the `sacct` command
for the desired period, save its output into a file, then download the file and use it with the scripts.

Example:
```
python run_sacct_only.py -S 2025-04-14 -E 2025-04-15 -a -o sacct_20250414.txt
```

In this case, the script will save the output of the command into a file (on the HPC machine) called `sacct_20250414.txt`.

Or, you could run `sacct` directly on the HPC. For example:
```
sacct --starttime 2025-04-14 --endtime 2025-04-15 \
  --format UID,User,JobID,JobName,Submit,Elapsed,Partition,NNodes,NCPUS,TotalCPU,CPUTime,ReqMem,MaxRSS,WorkDir,State,Account,AllocTres \
  -P -L --allusers > sacct_20250414.txt
```

Either way, you would download that file, and add the data into the database, using the `--useCustomLogs` option with the `run_backend.sh` script: 

```
sh scripts/backend/run_backend.sh \
   --db_name ga_db --db_user postgres --db_password <password> \
   --useOtherInfrastructureInfo ~/repos/GA4HPCdashboard/ga_dashboard/samples \             # NB absolute directory path
   --fixed_params_file ~/repos/GA4HPCdashboard/ga_dashboard/data/fixed_parameters.yaml \   # NB absolute file path
   --useCustomLogs path/to/downloaded/file/sacct_20250414.txt                              # NB absolute file path
```
Note that:
* The options for the start and end dates, `-S` and `-E`, are not needed, as the date range will be determined by the contents of the `sacct` output file.
* The directory given with the `--useOtherInfrastructureInfo` option must contain **both** the cluster information file (`cluster_info.yaml`) and the file listing the HPC users (`hpc_users_list.csv`); here, the `samples` subdirectory, which is part of the repo, is used.
* In this example, we use the file `sacct_20250414.txt`, which you just generated. Sample `sacct`-output files are also in the `samples` subdirectory. 


## Grafana set-up
A number of things need to be done, assuming you have downloaded Grafana and are running its server. These are:
* import the dashboard(s) you want to use into the Grafana server
* add teams and users (and their information) to the Grafana server

You must set the `--input_dir` argument, which specifies the directory containing your JSON files for the dashboards.

For example, if you wanted to use the demo dashboard directory, and other parameters set to default:

```
% python scripts/frontend/run_dashboard.py \
      --admin_password <grafana_admin_password> \
      --db_password <db_password> \
      --input_dir ga_dashboard/dashboards

```

You can specify many options for what you want, however; run the following to see your options:

```
% python scripts/frontend/run_dashboard.py -h
```
Here, relative paths are sufficient.

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

To use this dashboard, you would need to use the option `--name grafana-postgresql-ga_db` with `run_dashboard.py`.

[Back to Contents](../docs/Contents.md)
