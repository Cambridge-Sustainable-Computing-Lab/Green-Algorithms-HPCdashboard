# Setting up the demo

[Prerequisites](#prerequisites) - [Main installation](#main-installation) - [Database connection](#database-connection) - [Grafana setup](#grafana-setup)

## Introduction

The software has:

(1) Back-end: extracts job information from the HPC, and enhances this data

(2) Middle: writes this data to the Postgres database.

(3) Front-end: displays helpful dashboards using a Grafana server, which reads the relevant data from the Postgres database.

There are some helpful scripts in the `scripts/` directory of the repository (see below).

## Prerequisites

- Set up an environment for a suitable version of Python, e.g., by using [Miniconda](https://www.anaconda.com/docs/getting-started/miniconda/main). Then you can issue a command such as:

```
$ conda create -n py313 python=3.13 -c conda-forge
$ conda activate py313
$ python --version
Python 3.13.2
```
This example is for installing Python 3.13 (which is why we decided to call the environment `py313`). Your version may be different.

You will probably have to issue the `conda activate py313` command every time you log on to your machine.

If you need to exit the conda environment:
```
$ conda deactivate
```

- Install PostgreSQL locally or have access to a PostgreSQL server.
  - Choose a suitable password for the `postgres` user (do not leave as default).
  - Make sure you also have the `psql` script. On my Mac this is `/Library/PostgreSQL/17/bin/psql`. It would be good to prepend this directory to your `PATH` environment variable.
  - 


- Clone the repository:

```
$ git clone git@github.com:GreenAlgorithms/GA4HPCdashboard.git
```

So, on your machine, you should now have:

```
/some/path/or/other/GA4HPCdashboard
```
Navigate into this new `GA4HPCdashboard` directory.


## Database connection

#### DB installation

1. Create database “ga_db” as `postgres` user

```$ CREATE DATABASE ga_db;```

Example running it with the default **postgres** user:

```$ sudo -u postgres psql -c 'CREATE DATABASE ga_db;'```


2. Install the database (e.g. with the user **postgres**)

```
$ psql -h localhost -p 5432 -U postgres -d ga_db < ga_db.sql
````

4. Create a database user, with a password, which is read-only, and has access to the database tables. This will be used by Grafana to read information from the database.


## Grafana installation

Install the self-managed Grafana installation (Enterprise, just in case we want to host it on the cloud): [https://grafana.com/grafana/download?pg=get&plcmt=selfmanaged-box1-cta1](https://grafana.com/grafana/download?pg=get&plcmt=selfmanaged-box1-cta1).

In practice this involves downloading a `.tar.gz` file and unpacking it. The instructions should be on the Grafana download page.

## Grafana setup

## First run

Go to the Grafana directory and run the command:

```$ ./bin/grafana server```

Then log as admin on the web browser (admin:admin): [http://localhost:3000/](http://localhost:3000/).


### PostgreSQL

In Grafana go to $\color{green}{\textsf{Home > Connections > Data sources > Add data source}}$ and select **PostgreSQL**.

- Name: **grafana-postgresql-ga_db**
- Host URL: **localhost:5432**
- Database name: **ga_db** (for instance)
- TLS/SSL Mode: **disable** (for local installation)

### Run all setup in one command

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

Example of input file format (CSV format):
```
Name,User name,Email,Password,Team name
Thomas Greene,tg1,tg1@ga-test.com,<user_1_password>,Team 1
Adam Mackay,am1,am1@ga-test.com,<user_2_password>,Team 2
...
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

> [!NOTE]
> You can run the different steps individually via python scripts or manually via the Grafana web interface (see below).

### Setup data source

In the GA Project, the data source is a PostgreSQL database

#### Script version

Run the script `create_data_source.py`
For instance:
```
python create_data_source.py \
  --admin_login admin --admin_password <adm_password> \
  --db_name ga_db --db_user <db_user_name> --db_password <db_user_password> --pg_version 15
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
```

#### GUI version

You can create a data source via the web interface.

Go to $\color{green}{\textsf{Home > Connections > Datasources > + Add new data source (on the right hand-side) > PostgreSQL}}$.
Then you can create a data source by filling the form (we use the value 'disable' for the TLS/SSL Mode).

### Setup dashboards

#### Script version

The following script requires the installation of the packages listed in `requirements.txt`.

Run the script `import_dashboards.py`
For instance:
```
python import_dashboards.py --admin_login admin --admin_password <adm_password>
```

Options are:
```
  --input_dir INPUT_DIR: Dashboard files directory | default: ./dashboards/prod/
  --url URL: Grafana URL | default: localhost:3000
  --admin_login ADMIN_NAME: Grafana admin name | default: admin
  --admin_password ADMIN_PASS: Grafana admin password
  --dashboard_folder_name DASHBOARD_FOLDER_NAME: Name of the dashboard folder | default: Green Algorithms
```

#### GUI version

You can import the Dashboards [here](/frontend/dashboards/prod) on the repository.

Go to $\color{green}{\textsf{Home > Dashboards > New (on the right hand-side) > Import}}$ then import the JSON file (seems to work one by one).
Then you can create a directory (e.g. $\color{purple}{\textsf{Green Algorithms}}$) and move the newly imported dashboards there: it might be it easier to manage access at the folder level.

### Setup users and teams

#### Script version

The following script requires the installation of the packages listed in `requirements.txt`.

Run the script `import_users.py`
For instance
```
python import_users.py \
  --admin_login admin --admin_password <adm_password> --input_file <path_to_users_csv_file>
```

Options are:
```
  --input_file INPUT_FILE: User list in CSV format
  --url URL: Grafana URL | default: localhost:3000
  --admin_login ADMIN_NAME: Grafana admin name | default: admin
  --admin_password ADMIN_PASS: Grafana admin password
  --dashboard_folder DASHBOARD_FOLDER: Name of the dashboard folder | default: Green Algorithms
```

Example of input file format (CSV format):
```
Name,User name,Email,Password,Team name
Thomas Greene,tg1,tg1@ga-test.com,<user_1_password>,Team 1
Adam Mackay,am1,am1@ga-test.com,<user_2_password>,Team 2
...
```

#### GUI version

Some of the dashboards need to have a matching username to properly see all the panels.
For the example, I created a user $\color{orange}{\textsf{ll582}}$ which I included in a team $\color{darkred}{\textsf{Test}}$.

##### User

Go to $\color{green}{\textsf{Home > Administration > Users and access > Users > New User}}$
Then use the Username $\color{orange}{\textsf{ll582}}$.

##### Team

Go to $\color{green}{\textsf{Home > Administration > Users and access > Teams > New Team}}$.  
Then use the name $\color{darkred}{\textsf{Test}}$.
After that, click on the $\color{darkred}{\textsf{Test}}$ team and add $\color{orange}{\textsf{ll582}}$ as a new member.

Then go to the Dashboard directory $\color{purple}{\textsf{Green Algorithms > Folder actions (right hand-side) > Manage permissions}}$.  
Add permission for the team $\color{darkred}{\textsf{Test}}$ and remove roles Editor and Viewer (although not sure about removing those roles).

[Back to Contents](./Contents.md)
