# GA Grafana setup

## Prerequisites

- Install PostgreSQL locally or have access to a PostgreSQL server
- Install the database locally or on a PostgreSQL server (from the dump SQL)
- Download the Dashboard exports in JSON format: [dashboards/](/dashboards/)


## Main installation

Install the self-manage installation (Enterprise, just in case we want to host it on the cloud): [https://grafana.com/grafana/download?pg=get&plcmt=selfmanaged-box1-cta1](https://grafana.com/grafana/download?pg=get&plcmt=selfmanaged-box1-cta1)


## First run

Go to the Grafana directory and run the command:

```$ ./bin/grafana server```

Then log as admin on the web browser (admin:admin): [http://localhost:3000/](http://localhost:3000/).


## Database Connection

### PostgreSQL

In Grafana go to <span style="color:lightgreen">Home > Connections > Data sources > Add data source</span> and select **PostgreSQL**.

- Name: **grafana-postgresql-ga_db**
- Host URL: **localhost:5432**
- Database name: **ga_db** (for instance)
- TLS/SSL Mode: **disable** (for local installation)

#### DB installation:
1.	Create database “ga_db”:

```$ CREATE DATABASE ga_db;```

Example running it with the default **postgres** user:

```$ sudo -u postgres psql -c 'CREATE DATABASE ga_db;'```

2.	Download the SQL dump: [compressed database dump](/databases/ga_db_aggregate_2024-08-06.sql.gz)

3.	Install the database (e.g. with the user **postgres**):
```
$ gunzip ga_db_aggregate_2024-08-06.sql.gz
$ psql -h localhost -p 5432 -U postgres -d ga_db < ga_db_aggregate_2024-08-06.sql
````

## Dashboards

You can import the Dashboards [here](/dashboards/) on the repository.

Go to <span style="color:lightgreen">Home > Dashboards > New (on the right hand-side) > Import</span> then import the JSON file (seems to work one by one).  
Then you can create a directory (e.g. <span style="color:purple">Green Algorithms</span>) and move the newly imported dashboards there: it might be it easier to manage access at the folder level.


## Users/Groups

Some of the dashboards need to have a matching username to properly see all the panels.
For the example, I created a user “<span style="color:orange">ll582</span>” which I included in a team “<span style="color:darkred">Test</span>”.

### User
Go to <span style="color:lightgreen">Home > Administration > Users and access > Users > New User</span>
Then use the Username “<span style="color:orange">ll582</span>”.

## Team
Go to <span style="color:lightgreen">Home > Administration > Users and access > Teams > New Team</span>.  
Then use the name “<span style="color:darkred">Test</span>”.
After that, click on the “<span style="color:darkred">Test</span>” team and add “<span style="color:orange">ll582</span>” as a new member.

Then go to the Dashboard directory <span style="color:purple">Green Algorithms > Folder actions (right hand-side) > Manage permissions</span>.  
Add permission for the team "<span style="color:darkred">Test</span>” and remove roles Editor and Viewer (although not sure about removing those roles).
