# GA4HPCdashboard: Deployment notes

Repository used to set up the Green Algorithms dashboards, using [Grafana](https://grafana.com/) and a database. This allows you to examine HPC usage over time, with helpful graphs, charts, etc.

The system is composed of:
* A backend, which obtains usage data from the HPC system (using the `sacct` command), aggregates it (to one row per user per day), and enriches it (adds carbon footprint data).
* A PostgreSQL database to store the HPC usage calculated by the backend
* A frontend, which uses Grafana to query the database and display the data through graphs and charts.

### Contents
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
  * [Logging in to Grafana](#logging-in-to-Grafana)
* [Additional documentation](./docs/Contents.md)


Files required to deploy the dashboard (you will need your own versions of these):

* [Scripts configuration file](#configuration-files): template `config.txt` (in `configuration/templates/`) to copy and edit.
* [Cluster config file](#configuration-files): `cluster_info.yaml` (in `configuration/templates/`)
* [Dashboard users file](#list-of-users) `user_list.csv` (in `configuration/templates/`)
* [Fixed parameters file](#configuration-files). Example: `ga_dashboard/data/fixed_parameters.yaml`


---
## Prerequisites

### Python environment (Miniforge)
You will need to set up an environment for your Python distribution. We recommend you use Miniforge. 

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


### Install the `ga_dashboard` python package and its dependencies

In the top-level directory of the `GA4HPCdashboard` directory (i.e. one level above the `ga_dashboard` directory), type:

```
$ pip install -r requirements.txt
```
or
```
$ poetry install
```
based on which tool (`pip` or `poetry`) you prefer to use.

To install the `ga_dashboard` software package specifically, type:
```
$ python -m pip install .
```
(Note the period character at the end). This should install the `ga_dashboard` package on your local machine. If you want to be able to 
edit it and still use it, use the `-e` option:
```
$ python -m pip install -e .
```


### Database server - PostgreSQL
Install PostgreSQL locally or have access to a PostgreSQL server.

It is assumed that the operating system used to run the dashboard will be a flavour of UNIX/Linux. However, if you want to run it on a Mac, we suggest you use the relevant [Enterprise DB installer](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads) to start with. Regardless, follow the instructions for your system.

Later, it may be necessary to get a version of Postgres for your platform which supports ssh. This may require compiling Postgres yourself with the appropriate options. However, this is not needed for the simple demo. 

Choose a username and password for the Postgres admin user. The former is usually `postgres` (although you can choose what you want). Do not record this sensitive password in a file! In these instructions, we assume that the admin user name is `postgres`. (If you forget the password at any point, try [these steps](https://stackoverflow.com/questions/14588212/postgresql-resetting-password-of-postgresql-on-ubuntu).)

Check that your `$PATH` allows you to access the PostgreSQL `psql` utility program.


### Dashboard platform - Grafana

Install the [self-managed installation](https://grafana.com/grafana/download?pg=get&plcmt=selfmanaged-box1-cta1) (Enterprise, just in case we want to host it on the cloud).

By default, the super-user on Grafana is called `admin`, and has the password `admin`. You will probably want to change this, to make your set-up more secure.


---
## Configuration files

A number of config files are required by the system (e.g., to calculate the carbon footprint), as well as a list of dashboard users:

### System configuration files
As well as a list of dashboard users, the system needs:
* A **scripts configuration file** with all the required parameters (database connection, paths to the others configurations files, ...). You can:
  * Copy the template provided in `configuration/templates/config.txt` (e.g., to `<your_config_file.txt>`)
  * Replace all the parameters surrounded by the `< >` characters
  * Uncomment the optional parameters you want to use.
* **Information about your HPC cluster**.
  * Example: `configuration/examples/cluster_info__demo.yaml`.
  * Template: `configuration/templates/cluster_info.yaml`.
  * You will need to acquire the information about your own cluster, and present it in the same YAML format as the example file. Each partition (a set of computing nodes with a dedicated queue) will need information for `type` (CPU or GPU), `model` and `TDP`. This last you may have to find from data sheets on the internet. For partitions of `type` GPU, you will also need values for `model_CPU` and `TDP_CPU`. 
  * Note also that you will need values for the other items in the file: `institution`, `cluster_name`, `granularity_memory_request`, `PUE`, etc.
* **Fixed parameters file**. Example: `ga_dashboard/data/fixed_parameters.yaml`. We suggest you use this example file for now.



### List of users

This is a file with details of your Dashboard users, to collate their HPC use and create a Grafana account for them.

The users file should be a comma-separated file combining these columns:
* **User name**: Company/Institute user name (e.g. tg1)
* **User unique identifier** (UID): Numeric user unique idendifier (e.g. 11111)
* **Name**: Full user name (e.g. Thomas Greene)
* **Email**: email address of user
* **Group name**: Name of the user group/team (e.g. group 1)
* **Department name**: Name of the user department/unit (e.g. Dept 3)
* **GrafanaPassword**: Password required by this user for Grafana. By default, users only have view access.

For example in `configuration/examples/user_list__demo.csv`:
```
User,UID,Name,Email,Group,Department,GrafanaPassword
uid_1,11111,John Smith,user1@example.com,group_1,Dept_3,*0IK^I^&UpO$2aX
uid_2,22222,Sarah Jones,user2@example.com,group_1,Dept_3,yGg=kA-6v**7BS)
uid_3,33333,Tom Evans,user3@example.com,group_2,Dept_3,ibVvlpo$r7b0u
uid_4,44444,Lisa Bookbinder,user4@example.com,group_3,Dept_2,!3Q4o&%Fs5SE2
uid_5,55555,Ali Hassan,user5@example.com,group_4,Dept_1,qiY_pI%7BFz<JT
```

Displayed as a table:

| User | UID   | Name          | Email | Group   | Department | GrafanaPassword |
| -----|------ | ------------- | ------- | ---------- | ----| ------------ |
| uid_1 | 11111 | John Smith | user1@example.com | group 1 | Dept 3     | *0IK^I^&UpO$2aX |
| uid_2 | 22222 | Sarah Jones | user2@example.com   | group 1 | Dept 3     | yGg=kA-6v**7BS) |
| ...   | ...   | ...           | ...     | ...  | ...      | ... |


The passwords in the above example adhere to the [Grafana password policy](https://grafana.com/docs/grafana/next/setup-grafana/configure-security/configure-authentication/grafana/#strong-password-policy), should you decide to enforce it.

Make sure the passwords don't contain a comma character (`','`), otherwise this will affect the CSV file parsing.


### Using the same file for both
You may wish to have, as just described, one file of Grafana users and one of HPC users. For simplicity, you can use one file to combine both, provided all necessary fields are present. An example is available at `ga_dashboard/samples/sample_user_list.csv`.

Currently, the required fields are:

```
User,UID,Name,Email,Group,Department
```
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

**Note:** we have tested the software successfully on up to 1M jobs' log files (i.e. the `sacct` command returns one million entries). On a Mac, running the `scripts/run_green_algorithms_on_historical_logs.py` script on this data took 11m 42s **without the `sacct` runtime**, and the peak memory usage (measured with `mprof`) was around 4.7 GB.  This was an optimised situation; `sacct` had been run previously (and generated the file of results to use), and the files and Python scripts, Postgres database, and Grafana server were all running on the same local machine.

For the beta testing, you may want to restrict the dates to a few months to not have more than a few million jobs returned (until we have tested scalability in more details).

At the moment, all the data is read into memory for processing, before being written to the Postgres database.  We intend to update the code so that it only processes data (and writes it to the dataabse) in chunks, so that it can safely handle much more than this.

For a scheduled execution (e.g. a `cron` job), the command to run is:
```
$ python scripts/run_green_algorithms_on_logs.py --config <your_config_file.txt>
```
By default, it will collect the logs from yesterday (if no `startDay` / `endDay` are defined in the configuration file).

The 2 scripts proceed to:
* Collect the Slurm logs
* Enrich the logs, i.e., calculate carbon footprint data
* Aggregate the enriched data into one row per user per day
* Write the data to the database

> [!NOTE]
> The scripts above have the same admin user run the SLURM `sacct` command to download all the logs, process these logs, and add the processed data to the Postgres database. In some cases, it may not be suitable, e.g., if you want to run the `sacct` command on one machine, transfer the data to another one hosting the database and the two can't communicate directly. We haven't developed this alternative pipeline in the beta version quite yet, but if this is your case, do get in touch, we can walk you through separating the two parts of the code. 


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

Alternatively, you might need to use these steps to run the Grafana server after installation:

```
$ sudo /bin/systemctl daemon-reload
$ sudo /bin/systemctl enable grafana-server
$ sudo /bin/systemctl start grafana-server
```

#### Stop server
In the former case above, you can just CTRL-C the server. In the latter, you might have to do:

```
$ sudo /bin/systemctl stop grafana-server
```

The `systemctl` command might be elsewhere on a Linux system, e.g., `/usr/bin/systemctl`.

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



