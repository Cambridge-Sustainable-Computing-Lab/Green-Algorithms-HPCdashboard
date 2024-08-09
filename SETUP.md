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

## Dashboards

You can import the Dashboards [here](/dashboards/) on the repository.

Go to $\color{green}{\textsf{Home > Dashboards > New (on the right hand-side) > Import}}$ then import the JSON file (seems to work one by one).  
Then you can create a directory (e.g. $\color{purple}{\textsf{Green Algorithms}}$) and move the newly imported dashboards there: it might be it easier to manage access at the folder level.


## Users/Groups

Some of the dashboards need to have a matching username to properly see all the panels.
For the example, I created a user $\color{orange}{\textsf{ll582}}$ which I included in a team $\color{darkred}{\textsf{Test}}$.

### User

Go to $\color{green}{\textsf{Home > Administration > Users and access > Users > New User}}$
Then use the Username $\color{orange}{\textsf{ll582}}$.

## Team

Go to $\color{green}{\textsf{Home > Administration > Users and access > Teams > New Team}}$.  
Then use the name $\color{darkred}{\textsf{Test}}$.
After that, click on the $\color{darkred}{\textsf{Test}}$ team and add $\color{orange}{\textsf{ll582}}$ as a new member.

Then go to the Dashboard directory $\color{purple}{\textsf{Green Algorithms > Folder actions (right hand-side) > Manage permissions}}$.  
Add permission for the team $\color{darkred}{\textsf{Test}}$ and remove roles Editor and Viewer (although not sure about removing those roles).
