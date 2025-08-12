# GA4HPCdashboard: Deployment notes

Repository used to setup the Green Algorithms dashboards, using [Grafana](https://grafana.com/) and a database. This allows you to examine HPC usage over time, with helpful graphs, charts, etc.

The system is composed of:
* A backend, which obtains usage data from the HPC system (using the `sacct` command), aggregates it (to one row per user per day), and enriches it (adds carbon footprint data).
* A PostgreSQL database to store the HPC usage calculated by the backend
* A frontend, which uses Grafana to query the database and display the data through graph and charts.

Content
* [Prerequisites](#prerequisites)
  * [Python environment](#python-environment-miniforge)
  * [`ga_dashboard` python package](#install-the-ga_dashboard-python-package)
  * [Database server](#database---postgresql)
  * [Dashboard platform - Grafana](#dashboard-platform---grafana)
* [Configuration files](#configuration-files)
  * [System configuration files](#system-configuration-files)
  * [Dashboard users file](#list-of-users)
* [Install Green Algorithms dashboard](#install-green-algorithms-dashboard)
* [HPC usage data collection](#hpc-usage-data-collection)
* [Green Algorithms dashboards](#green-algorithms-dashboards)
  * [Run Grafana server](#run-grafana-server)
  * [Setup dashboards and users](#setup-dashboards-and-users)
  * [Logging in to Grafana](#logging-in-to-Grafana)
* [Additional documentation](./docs/Contents.md)


Files required to deploy the dashboard (you will need your own versions of these):

* [Scripts configuration file](#configuration-files): template `config_templates.txt` (in `scripts/`) to copy and edit.
* [Cluster config file](#configuration-files): `cluster_info.yaml` (in `docs/templates/`)
* [Dashboard users file](#list-of-users) `sample_user_list.csv` (in `docs/templates/`)
* [Fixed parameters file](#configuration-files). Example: `ga_dashboard/data/fixed_parameters.yaml`


---
## Prerequisites

### Python environment (Miniforge)
You will need tp set up an environment for your Python distribution. We recommend you use Miniforge. 

Go to the [download link](https://conda-forge.org/download/) and follow the instructions for your platform. You may need to look at the instructions on their [GitHub repository](https://github.com/conda-forge/miniforge).

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


### Install the `ga_dashboard` python package
We assume you have `git` installed on your system.

In the top-level directory of the `GA4HPCdashboard` directory (i.e. one level above the `ga_dashboard` directory), type:
```
$ python -m pip install .
```
This should install the `ga_dashboard` package on your local machine. if you want to be able to 
edit it and still use it, use the `-e` option:
```
$ python -m pip install -e .
```


### Database server - PostgreSQL
Install PostgreSQL locally or have access to a PostgreSQL server

For Macs, we have used the relevant [Enterprise DB installer](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads) to start with. Follow the instructions for your system.

Later, it may be necessary to get a version of Postgres for your platform which supports ssh. This
may require compiling Postgres yourself with the appropriate options. However, this is not
needed for the simple demo. 

Choose a username and password for the Postgres admin user. The former is usually `postgres` (although you can choose what you want). Do not record the password in a file! (In these instructions, we assume that the admin user name is `postgres`.) (If you forget the password at any point, try [these steps](https://stackoverflow.com/questions/14588212/postgresql-resetting-password-of-postgresql-on-ubuntu).)

Check that your `$PATH` allows you to access the PostgreSQL `psql` utility program.


### Dashboard platform - Grafana

Install the [self-managed installation](https://grafana.com/grafana/download?pg=get&plcmt=selfmanaged-box1-cta1) (Enterprise, just in case we want to host it on the cloud).


---
## Configuration files

A number of config files are required by the system (e.g., to calculate the carbon footprint), as well as list of dashboard users:

### System configuration files
As well as a list of dashboard users, the system needs:
* A **scripts configuration file** with all the required parameters (database connection, paths to the others configurations files, ...). You can:
  * Copy the template provided in `scripts/config_templates.txt`
  * Replace all the parameters surrounded by the `< >` characters
  * Uncomment the optional parameters you want to use.
* **Information about your HPC cluster**. Example: `docs/templates/cluster_info.yaml`.
* **Fixed parameters file**. Example: `ga_dashboard/data/fixed_parameters.yaml`.


### List of users

You will need a file with details of your Dashboard users. For each, you will obtain their `sacct` data, and add them to the Postgres database and the Grafana instance.
The users file should be a comma-separated file combining these columns:
* **User name**: Company/Institute user name (e.g. tg1)
* **User unique idendifier** (UID): Numeric user unique idendifier (e.g. 11111)
* **Name**: Full user name (e.g. Thomas Greene)
* **Email**: email address of user
* **Group name**: Name of the user group/team (e.g. group 1)
* **Department name**: Name of the user department/unit (e.g. Dept 3)

For example in `docs/templates/sample_user_list.csv`:
```
User,UID,Name,Email,Group,Department
uid_1,11111,John Smith,user1@example.com,group_1,Dept_3
uid_2,22222,Sarah Jones,user2@example.com,group_1,Dept_3
uid_3,33333,Tom Evans,user3@example.com,group_2,Dept_3
uid_4,44444,Lisa Bookbinder,user4@example.com,group_3,Dept_2
uid_5,55555,Ali Hassan,user5@example.com,group_4,Dept_1
```

Displayed as a table:

| User | UID   | Name          | Email | Group   | Department |
| -----|------ | ------------- | ------- | ---------- | ----|
| uid_1 | 11111 | John Smith | user1@example.com | group 1 | Dept 3     |
| uid_2 | 22222 | Sarah Jones | user2@example.com   | group 1 | Dept 3     |
| ...   | ...   | ...           | ...     | ...  | ...      |


The passwords generated by the scripts adhere to the [Grafana password policy](https://grafana.com/docs/grafana/next/setup-grafana/configure-security/configure-authentication/grafana/#strong-password-policy), if you decide to enforce it.


---
## Install Green Algorithms dashboard

After the creation of your scripts configuration file (cf. [Configuration files](#configuration-files)), you can run the script below to:
* Create the database (empty).
* Insert the list of dashboard users into this database.
* Setup Grafana:
  * Link the database to Grafana
  * Create the Green Algorithms folder (on Grafana) and import the dashboard(s) into it.
  * Add the dashboard users to Grafana.
  * Setup Grafana folder permissions for the users.

```
$ python scripts/install_GAdashboard.py --config <your_config_file.txt>
```
This will prompt you to enter the Grafana admin password and the PostgreSQL user password.


---
## HPC usage data collection
The dashboard extracts usage information from the HPC system. 

Each user will need to be added to Postgres.

To run it for the first time, the command is:
```
$ python scripts/run_green_algorithms_on_historical_logs.py --config <your_config_file.txt>
```
This will collect all the logs available by default (if no `startDay` / `endDay` are defined in the configuration file).

Note: we have tested the software successfully with a `sacct`-output data file of more than one million entries. Our intention is to update the software so that it can safely handle much more than this.

For a scheduled execution (e.g. a `cron` job), the command to run is:
```
$ python scripts/run_green_algorithms_on_logs.py --config <your_config_file.txt>
```
By default, it will collect the logs from yesterday (if no `startDay` / `endDay` are defined in the configuration file).

The 2 scripts proceed to:
* Collect the Slurm logs
* Enrich the logs, i.e. calculate carbon footprint data
* Aggregate the enriched data into one row per user per day
* Write the data to the database

> [!NOTE]
> Both scripts will run the `sacct` command (on HPC) unless you use the `useCustomLogs` in the scripts configuration file. See below how to use the `useCustomLogs` parameter.

The (anonymised) examples of files you can use with `useCustomLogs` are:

* `docs/templates/sacct_output_single_user.txt`
  > Example of output generated, for one user, by the `sacct` command on the HPC system.
* `docs/templates/sacct_output_multi_user.txt`
  > Same example as above, but for multiple users.

The backend part of the software will aggregate the data into one row per user per day, enrich it (add carbon footprint data), and then write this to the database. 

In order to do this, you need to uncomment `useCustomLogs` and set it with a value (e.g. `docs/templates/sacct_output_multi_user.txt`) in your scripts configuration file before running: 

```
$ python scripts/run_green_algorithms_on_logs.py --config <your_config_file.txt>
```

NB In order to run the `sacct` command, the scripts will need to run on the HPC system. Other than that, you can run them on your local machine.

---
## Green Algorithms dashboards

### Run Grafana server

#### Start server

By default, Grafana displays dates in US format. If you'd like them in your local date format, run this command (or put it in your shell config):
```
$ export GF_DATE_FORMATS_USE_BROWSER_LOCALE=true
```

In the same shell, `cd` to the Grafana directory and start the server:

```
$ cd /.../grafana/
$ ./bin/grafana server
```

Depending on your system, you may not be able to do this. For example, on Linux, you might need to use these steps to run the Grafana server after installation:

```
$ sudo bin/systemctl daemon-reload
$ sudo bin/systemctl enable grafana-server
$ sudo bin/systemctl start grafana-server
```

#### Stop server
In the former case above, you can just CTRL-C the server. In the latter, you might have to do:

```
$ sudo bin/systemctl stop grafana-server
```

the `systemctl` command might be elsewhere on a Linux system, e.g., `/usr/bin/systemctl`.

Once you have started Grafana on your system, log in as admin on the web browser (Default: admin, admin): [http://localhost:3000/](http://localhost:3000/).  


### Logging in to Grafana
By default, only the administrator (default name: admin) is allowed to edit dashboards. Although you can allow other users to do so.

> [!IMPORTANT]  
> You should change the admin password to something else, to reduce the likelihood of being hacked.

In the following, you can click on the screenshots to enlarge them.

Let's assume you want to log in as a basic user (not an admin). If you point your browser to port 3000, you should see something like this, if Grafana is running:

![Grafana login screen.](./docs/images/grafana_login_screen.png)

Assuming you now enter the login details for a user, you should see something like this:

![Grafana welcome screen.](./docs/images/grafana_welcome_screen.png)

Click on "Dashboards" in the menu at the left of the screen. A new screen should then load:

![Grafana dashboards screen.](./docs/images/dashboards.png)

If you click the little arrow to the left of "Green Algorithms", you should see "User" listed. If you then click on that, you should be taken to the User dashboard:

![Grafana "User" dashboard.](./docs/images/user.png)

> [!NOTE]
> The data you see will depend on (1) which data you loaded into the PostgreSQL database, and (2) the time range you select (which you can either do with the panel near the top-right of the dashboard, or by manually selecting a time range from one of the time series plots.)

For this to work, it assumes you have the PostgreSQL database set up as a "data source" in Grafana (this is done for you automatically by the installation script).



