# GA4HPCDASHBOARD

Repository used to setup the Green Algorithms dashboards, using [Grafana](https://grafana.com/) and a database.

The instructions for running the end-to-end demo are a little different. See bottom of page.


## Prerequisites

### Database - PostgreSQL

- Install PostgreSQL locally or have access to a PostgreSQL server
- Install the database locally or on a PostgreSQL server (from the dump SQL)

### Dashboard platform - Grafana

Install the self-manage installation (Enterprise, just in case we want to host it on the cloud): [https://grafana.com/grafana/download?pg=get&plcmt=selfmanaged-box1-cta1](https://grafana.com/grafana/download?pg=get&plcmt=selfmanaged-box1-cta1)

### Generate a users file - csv format

The users file should be a comma-separated file combining these columns:
* **Name**: Full user name (e.g. Thomas Greene)
* **User name**: Company/Institute user name (e.g. tg1)
* **Email**: Company/Institute user email (e.g. tg1@ga-test.com)
* **Password**: Temporary password (could be automatically generated)
* **Team name**: Name of the user team/department/unit (e.g. Team 1)

Example of input file format (CSV format with header):
```
Name,User name,Email,Password,Team name
Thomas Greene,tg1,tg1@ga-test.com,<user_1_password>,Team 1
Adam Mackay,am1,am1@ga-test.com,<user_2_password>,Team 2
...
```
Display as a table:
| Name          | User name | Email           | Password          | Team name |
| ------------- | --------- | --------------- | ----------------- | --------- |
| Thomas Greene | tg1       | tg1@ga-test.com | *user_1_password* | Team 1    |
| Adam Mackay   | am1       | am1@ga-test.com | *user_2_password* | Team 2    |
| ...           | ...       | ...             | ...               | ...       |


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
psql -h <db_host> -p 5432 -U <db_user_with_write_access> -d ga_db /.../ga_data_aggregate_table_schema.sql
```
> [!NOTE]
> This step could be embedded into a script


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


## Running the end-to-end demo
The end-to-end demo script, `demo.sh`:
* **Deletes any existing instance of the Postgres `ga_db` database!**
* Creates a new `ga_db` Postgres database (with unpopulated tables). 
* Runs the backend code to read an example `sacct` output file, transform the data, and write it to the Postgres database
* Runs the code to add users to both Grafana and `ga_db`
* Loads Postgres into Grafana as a "data source" for the latter
* Loads a simple dashboard, which reads the data just inserted in `ga_db` and displays graphs, etc.

The idea of this script is to illustrate the entire process, from `sacct` file generation to dashboard viewing.

To run the demo, the pre-requisites are:
* You must have installed Postgres, and have the name and password for a user with write access (such as the `postgres` user)
* You must have downloaded Grafana and started running the server.


The simplest version runs everything on the same machine. However, there are plenty of configuration options in the `demo.sh` script, which you can override if you don't want to use the default values provided.

To run the script, assuming your Postgres user's password is ilovecats:

```
cd GA4HPCdashboard
sh ./demo.sh ilovecats
```
Make sure there are no connections to the Postgres database before you run the script. This may require you to restart the grafana server, if it has an existing connection to it.

All being well, you will see output to your terminal, ending with:
```
******* Demo script completed. *******
```

The users file is used for both the frontend (Grafana users) and back-end (HPC users):

```
User,UID,Name,GrafanaPassword,Email,Group,Department
uid_1,11111,User_1,password1,user1@example.com,group_1,Dept_3
uid_2,22222,User_2,password2,user2@example.com,group_1,Dept_3
...
```
Displayed as a table:

| User  | UID   | Name   | GrafanaPassword | Email             | Group   | Department |
| ----- | ------| -------| --------------- | ----------------- |---------|------------|
| uid_1 | 11111 | User_1 | password1       | user1@example.com | group_1 | Dept_3     |
| uid_2 | 22222 | User_2 | password2       | user2"example.com | group_1 | Dept_3     |
| ...   | ...   | ...    | ...             | ...               | ...     | ...        |

The "teams" in the original dashboard version are the "Groups" in the end-to-end version.

Note: none of the example data in this file have a space character. We need to check it all works OK with names like "Thomas Greene", groups like "Weston group", and departments like "Department of Time Travel".

You will need to navigate to the "dashboards" menu on the Grafana server (in a web browser), and there select the Green Algorithms Demo dashboard.