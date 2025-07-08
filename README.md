# GA4HPCDASHBOARD: Deployment notes

Repository used to setup the Green Algorithms dashboards, using [Grafana](https://grafana.com/) and a database. This allows you to examine HPC usage over time, with helpful graphs, charts, etc.

(The instructions for running the end-to-end demo are a little different. See [documentation](./docs/end-to-end.md).

There are a number of scripts you can use to set-up the system with default values. You can either use these directly, or (recommended) use the wrapper script `scripts/run.py`, in which case you will need to ensure the values in `scripts/sample_config.txt` (or another config file of your choice). 

```
$ python scripts/run.py --help
usage: run.py [-h] [--config CONFIG_FILE]

User-friendly interface to the different scripts.

options:
  -h, --help            show this help message and exit
  --config CONFIG_FILE  Name of config file for your parameter values.

Uses sample config file by default.
```
The wrapper script calls the individual scripts under the hood.

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
[7] Do [4], [5] and [6] in one go (invokes run_dashboard.py).
[8] Run sacct command, and generate logfile, ON YOUR HPC SYSTEM.
[9] Run backend ON YOUR HPC SYSTEM (run sacct, enrich data with carbon footprint info, and add it to database).
> 
```


But you will need to set a few things up first, however you use the scripts.


[Documentation contents](./docs/Contents.md)

[More info on scripts](./scripts/README.md)

## Prerequisites

You will probably want to set up an environment for your Python dictribution. We used miniconda. Go to the [miniconda download link](https://www.anaconda.com/download/success) and follow the instructions for your platform.

Then, once installed, you can create an environment for a suitable version of python. For example:
```
$ conda create -n py313 python=3.13 -c conda-forge
$ conda activate py313
```
To leave the environment, type:
```
$ conda deactivate
```
To see your list of environments, type:
```
$ conda env list
```

## Install the `ga_dashboard` package
We assume you have `git` installed on your system. 

(In my case, I was working on a Mac. First, I had to install [`brew`](https://brew.sh/). And install the Xcode command-line tools. Then I was able to install `git`.)

In the top-level directory of the `GA4HPCdashboard` directory (i.e. one level above the `ga_dashboard` directory), type:
```
python -m pip install .
```
This should install the `ga_dashboard` package on your local machine. if you want to be able to 
edit it and still use it, use the `-e` option:
```
python -m pip install -e .
```

### Database - PostgreSQL

- Install PostgreSQL locally or have access to a PostgreSQL server


For Macs, we have used the relevant [Enterprise DB installer](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads) to start with. Follow the instructions for your system.

Later, it may be necessary to get a version of Postgres for your platform which supports ssh. This
may require compiling Postgres yourself with the appropriate options. However, this is not
needed for the simple demo. 

Choose a username and password for the admin user. The former is usually `postgres` (although you can choose what you want). Do not record the password in a file! (In these instructions, we assume that the admin user name is `postgres`.)

Check that your `$PATH` allows you to access the PostgreSQL `psql` utility program.

### Backend data
The dashboard extracts usage information from the HPC system. Three (anonymised) examples of files you can use are:

* `ga_dashboard/samples/sacct_output_single_user.txt`
* `ga_dashboard/samples/sacct_output_multi_user.txt`
* `ga_dashboard/samples/userDaily_mockMultiUsers_1.csv`

The first file is an example of output generated, for one user, by the `sacct` command on the HPC system. This can be used if you want/need to 
import data into the database for testing, or if (say) you cannot get data from the HPC system. The second file is similar, but for multiple users. You need to make sure you have a list of HPC users in the database (q.v.). With both of these files, the backend part of the software will aggregate the data into one row per user per day, enrich it (add carbon footprint data), and then write this to the database. 

In order to do this, you can either execute the relavent script directly:

```
$ python scripts/backend/run_backend.py --useCustomLogs ga_dashboard/samples/sacct_output_multi_user.txt --db_password <password>
```

Or, use the wrapper script option 9, and set the `useCustomLogs` option in the wrapper config file to the file you want. (In normal operation, in which we query the HPC by running `sacct`, this option should be commented-out in the config file.)

The third file can be imported directly into the database, as it has already been aggregated and enriched. You can use option 2 of the wrapper script `run.py` to do this.

Of course, you don't have to use our sample files; you can get your own from your HPC system. Normally, you will either use option 8 or 9. Both options will run the `sacct` command. Option 9 will aggregate the data into one row per user per day, and enrich it with carbon footprint information, and write it to the database. That assumes your HPC node running the script can connect to your database. The alternative is to run option 8, which will save the output of the `sacct` command to a log file, which you can then download to a local machine, then load into the database using option 9 and the appropriate value for the `useCustomLogs` option in the wrapper config file, as described above. 

### Dashboard platform - Grafana

Install the self-manage installation (Enterprise, just in case we want to host it on the cloud): [https://grafana.com/grafana/download?pg=get&plcmt=selfmanaged-box1-cta1](https://grafana.com/grafana/download?pg=get&plcmt=selfmanaged-box1-cta1)

### Generate a Grafana users file - csv format

The users file should be a comma-separated file combining these columns:
* **Name**: Full user name (e.g. Thomas Greene)
* **User name**: Company/Institute user name (e.g. tg1)
* **Email**: Company/Institute user email (e.g. tg1@ga-test.com)
* **Team name**: Name of the user team/department/unit (e.g. Team 1)

Example of input file format (CSV format with header):
```
Name,User name,Email,Team name
Thomas Greene,tg1,tg1@ga-test.com,Team 1
Adam Mackay,am1,am1@ga-test.com,Team 2
...
```
Display as a table:
| Name          | User name | Email           |  Team name |
| ------------- | --------- | --------------- | ---------- |
| Thomas Greene | tg1       | tg1@ga-test.com |  Team 1    |
| Adam Mackay   | am1       | am1@ga-test.com |  Team 2    |
| ...           | ...       | ...             |  ...       |

Note that, for security reasons, passwords are not stored in this file. Passwords will be automatically generated (to be noted, or acted on by your setup in some other way) when users are added to the Grafana Dashboard by the `import_users.py` script (or the wrapper script).

An example you can use to try out the system is `ga_dashboard/samples/grafana_users_list.csv`

## Setup Green Algorithms dashboards


### Start Grafana

Go to the Grafana directory and run the command:

```
$ cd /.../grafana/
$ ./bin/grafana server
```

Then log as admin on the web browser (admin:admin): [http://localhost:3000/](http://localhost:3000/).  


### Setup database - PostgreSQL

1. Create database “**ga_db**”

```$ CREATE DATABASE ga_db;```

Example running it with the default **postgres** user:

```$ sudo -u postgres psql -c 'CREATE DATABASE ga_db;'```

2. Load the database schema (e.g. with the user **postgres**)  
The database schema is located under the "**databases**" directory. 
```
psql -h <db_host> -p 5432 -U <db_user_with_write_access> -d ga_db ga_db.sql
```



### Run GA4HPCDASHBOARD script

The script `ga_dashboard.py` runs sequentially the code to:

* Create the data source
* Create the dashboards folder
* Import the dashboards
* Create users and teams


For instance
```
python ga_dashboard.py \
  --admin_login admin --admin_password <adm_password> \
  --db_name ga_db --db_user <db_user_name> --db_password <db_user_password> --pg_version 15 \
  --input_file <path_to_users_csv_file>
```

Options are:
```
  --name DS_NAME: Data source name | default: grafana-postgresql-ga_db
  --url URL: Grafana URL | default: localhost:3000
  --admin_login ADMIN_NAME: Grafana admin name | default: admin
  --admin_password ADMIN_PASS: Grafana admin password
  --db_name DB_NAME: Database name
  --db_user DB_USER: Database user name
  --db_password DB_PASSWORD: Database user password
  --db_host DB_HOST: Database host | default: localhost
  --db_port DB_PORT: Database port | default: 5432
  --pg_version PG_VERSION: PostgreSQL version | default: 13
  --dashboard_folder_name DASHBOARD_FOLDER_NAME: Name of the dashboard folder | default: Green Algorithms
  --input_dir INPUT_DIR: Dashboard files directory
  --input_file INPUT_FILE: User list in CSV format
```

### Import logs data

Import logs data via the [GreenAlgorithms4HPC](https://github.com/GreenAlgorithms/GreenAlgorithms4HPC) repository.

