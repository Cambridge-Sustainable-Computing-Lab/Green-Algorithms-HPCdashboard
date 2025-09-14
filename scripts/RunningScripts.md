# Running the scripts
The software comprises:
1. A database
2. A backend (to query SLURM for data, enrich this data, and store it in the database)
3. A frontend (which uses Grafana to query the database and display nice charts, etc.)

The scripts in these directories can be used to run the entire cycle:

1. Initialise the PostgreSQL database
2. Running the backend (run `sacct` command, enhance the data and load it into the database)
3. Set up the dashboards, users, etc.

It should then be possible to view the data in the dashboards running on the Grafana server.

## User-friendly wrapper script
There is a "wrapper" script around the other scripts. This uses a config file to save you lots of
tedious typing out of command-line arguments. This script is `scripts/run.py`, and the default
config file is `scripts/sample_config.txt`. You can either use that, or set up your own
config file. 

DO NOT STORE PASSWORDS IN THESE FILES! You wil be asked for passwords as and when
required by the wrapper script. The wrapper script does not display these on the screen.

The instructions below tell you how to use each script, if you want to use them directly,
but it is recommended that you use the wrapper script, which should be fine for most cases.
There are one or two obscure arguments used by some scripts, and you can always use them
directly in the unlikely event that the wrapper can't do what you want. The scripts have 
a `--help` option to display the different arguments. 

The wrapper script continually asks for input. This is what it looks like:
```
$ python scripts/run.py 

Using config file scripts/sample_config.txt
Select option:
[q] Exit.
[1] Import HPC users into database.
[2] Import already-aggregated, mock-up data into database.
[3] Create or overwrite database.
[4] Create a data source in Grafana for dashboard to connect to.
[5] Import dashboard(s) into a Grafana folder.
[6] Generate user passwords, import users to Grafana, and set their folder permissions.
[7] Do [4], [5] and [6] in one go (invokes setup_frontend.py).
[8] Run sacct command, and generate logfile, ON YOUR HPC SYSTEM.
[9] Run backend ON YOUR HPC SYSTEM (run sacct, enrich data with carbon footprint info, and add it to database).
> 
```

## Other points

If in doubt, use the absolute paths of files and directories when passing arguments to the scripts. Some scripts sometimes allow use of relative paths.

It is envisaged that the first time the backend is run, the data obtained by `sacct` will be that of all the jobs (that the system still has a record of)
which occurred before the current time (perhaps upto the end of the previous day). These would then be loaded into the database, and viewable with the
dashboard.

It is also envisaged that, after this, the backend process will be run as a daily `cron` job, continually updating the database with details of HPC usage,
perhaps over the previous 24 hours or 7 days, say.

Users will need to be added to the HPC users file before running the backend, as the code currently raises an error if a job is encountered
in the `sacct` output with a User which the backend hasn't been told about.

## Database set-up
This assumes you have installed PostgreSQL, and have a suitable admin user for it.

Use `create_or_overwrite_database.py` (or option 3 of the wrapper script).

Example:
```
python scripts/database/create_or_overwrite_database.py --db-password mypassword
```
It uses a lot of default arguments. Run the script with `--help` to see them.

> [!WARNING]
> This will create a new database with empty tables. If you run it and the database already exists, it will delete your data, as its name suggests.

You will be prompted for the password of your db admin-user (possibly your `postgres` user). This gives you the chance to CTRL-C out if you invoked it by mistake.

<ins>**WARNING!! This script will delete any existing instance of the database, including all its data, so only run this if you are sure that's what you want.**</ins>

To add HPC users to this database, use the `add_users_to_database.py` script with your db admin--user password (or option 1 of the wrapper script). For example:
```
python scripts/database/add_users_to_database.py \
    --db_name ga_db --db_user postgres --db_port 5432 --db_host localhost \
    --input_file docs/templates/sample_user_list.csv --db_password <your_password>
```

Note that we want to add HPC users to the database before running `sacct`; the users we want should exists in the backend database regardless of whether there is any `sacct` data for them!


## Extract data with `sacct`, and enrich it
We assume that the usual case is that you are able to run the code/scripts for setting up the database, etc., on the same HPC system where you run the `sacct` command.

If so, invoke the `run_backend.py` script **without** the `--useCustomLogs` option. For example:

```
python scripts/backend/run_backend.py --db_password <password> 
                                      --startDay 2025-04-14 --endDay 2025-07-27
```
Run the script with `--help` to see the default values it is using.

This will extract usage information using `sacct`, enrich it (work out some additional quantities using it), then add it to the database. Obviously, you will need to change the values passed as the script arguments to your own set-up.


However, assuming you **cannot** run the code/scripts on the HPC system, you will need to run just the `sacct` command
for the desired period, save its output into a file, then download the file and use it with the scripts.

Example:
```
python scripts/backend/run_sacct_only.py 
    --startDay 2025-04-14 --endDay 2025-07-27 --outFile sacct_2025_07_27.txt
```

In this case, the script will save the output of the command into a file (on the HPC machine) called `sacct_20250414.txt`.

Or, you could run `sacct` directly on the HPC. For example:
```
sacct --starttime 2025-04-14 --endtime 2025-07-27 \
  --format UID,User,JobID,JobName,Submit,Elapsed,Partition,NNodes,NCPUS,TotalCPU,CPUTime,ReqMem,MaxRSS,WorkDir,State,Account,AllocTres \
  -P -L --allusers > sacct_2025_07_27.txt
```

Either way, you would download that file, and add the data into the database, using the `--useCustomLogs` option with the `run_backend.py` script: 

```
python scripts/backend/run_backend.py --db_password <password> \
      --useCustomLogs path/to/downloaded/file/sacct_2025_07_27.txt
```
Note that:
* The options for the start and end dates are not needed, as the date range will be determined by the contents of the `sacct` output file.
* In this example, we use the file `sacct_2025_07_27.txt`, which you just generated. Sample `sacct`-output files are also in the `tests/testdata` subdirectory. 


## Grafana set-up
A number of things need to be done, assuming you have downloaded Grafana and are running its server. These are:
* import the dashboard(s) you want to use into the Grafana server
* add teams and users (and their information) to the Grafana server

By default, the `--input_dir` argument, which specifies the directory on disk containing your JSON files for the 
dashboards, will use the examples provided in `ga_dashboard/dashboards`. If you wish to use another directory, 
you must set this option to the location you want.

For example, if you wanted to use the demo dashboard directory, and other parameters set to default:

```
% python scripts/frontend/setup_frontend.py \
      --admin_password <grafana_admin_password> \
      --db_password <db_password>
```

You can specify many options for what you want, however; run the following to see your options:

```
% python scripts/frontend/setup_frontend.py -h
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

To use this dashboard, you would need to use the option `--name grafana-postgresql-ga_db` with `setup_frontend.py`.

[Back to Contents](../docs/Contents.md)
