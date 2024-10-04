# GA Grafana setup

## Prerequisites

- Install PostgreSQL locally or have access to a PostgreSQL server
- Install the database locally or on a PostgreSQL server (from the dump SQL)
- Download the Dashboard exports in JSON format: [dashboards/prod/](/dashboards/prod/)

## Main installation

Install the self-manage installation (Enterprise, just in case we want to host it on the cloud): [https://grafana.com/grafana/download?pg=get&plcmt=selfmanaged-box1-cta1](https://grafana.com/grafana/download?pg=get&plcmt=selfmanaged-box1-cta1)


## First run

Go to the Grafana directory and run the command:

```$ ./bin/grafana server```

Then log as admin on the web browser (admin:admin): [http://localhost:3000/](http://localhost:3000/).


## Database Connection

### PostgreSQL

In Grafana go to $\color{green}{\textsf{Home > Connections > Data sources > Add data source}}$ and select **PostgreSQL**.

- Name: **grafana-postgresql-ga_db**
- Host URL: **localhost:5432**
- Database name: **ga_db** (for instance)
- TLS/SSL Mode: **disable** (for local installation)

#### DB installation

1. Create database “ga_db”

```$ CREATE DATABASE ga_db;```

Example running it with the default **postgres** user:

```$ sudo -u postgres psql -c 'CREATE DATABASE ga_db;'```

2. Download the SQL dump: [compressed database dump](/databases/ga_db_aggregate.sql.gz)

3. Install the database (e.g. with the user **postgres**)

```
$ gunzip ga_db_aggregate.sql.gz
$ psql -h localhost -p 5432 -U postgres -d ga_db < ga_db_aggregate.sql
````

## Grafana setup

### Dashboards

#### Script version

The following script requires the installation of the packages listed in `requirements.txt`.

Run the script `import_dashboards.py`
For instance
```
python import_dashboards.py --admin_login admin --admin_password <adm_password>
```

Options are:
```
  --input_dir INPUT_DIR: Dashboard files directory
  --url URL: Grafana URL
  --admin_login ADMIN_NAME: Grafana admin name
  --admin_password ADMIN_PASS: Grafana admin password
  --dashboard_folder_name DASHBOARD_FOLDER_NAME: Name of the dashboard folder
```

#### GUI version

You can import the Dashboards [here](/dashboards/prod) on the repository.

Go to $\color{green}{\textsf{Home > Dashboards > New (on the right hand-side) > Import}}$ then import the JSON file (seems to work one by one).  
Then you can create a directory (e.g. $\color{purple}{\textsf{Green Algorithms}}$) and move the newly imported dashboards there: it might be it easier to manage access at the folder level.

### Users/Groups

#### Script version

The following script requires the installation of the packages listed in `requirements.txt`.

Run the script `import_users.py`
For instance
```
python import_users.py --admin_login admin --admin_password <adm_password> --input_file <path_to_users_csv_file>
```
Options are:
```
  --input_file INPUT_FILE: User list in CSV format
  --url URL: Grafana URL
  --admin_login ADMIN_NAME: Grafana admin name
  --admin_password ADMIN_PASS: Grafana admin password
  --dashboard_folder DASHBOARD_FOLDER: Name of the dashboard folder
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
