# Guide to using configuration templates

The different configurations that must be set up before running the Green Algorithms Dashboard are:
1. [config.yaml](#scripts-configuration-configyaml)
2. [cluster_info.yaml](#cluster-information-cluster_infoyaml)
3. [user_list.csv](#dashboard-users-user_listcsv)

It is important to edit these and configure them to make the GA Dashboard work for your system.

## Scripts Configuration ([config.yaml](templates/config.yaml))

This is your master configuration file. It tells the Dashboard where to find your other config files, how to connect to Grafana and PostgreSQL, and how to run. It is split into five sections:

- **Config file paths**: locations of the other files the Dashboard depends on (`cluster_info.yaml`, the user list, and the fixed parameters file).
- **Database config**: connection details for the PostgreSQL database that stores user details, processed logs data, and average carbon intensity values (UK only).
- **Grafana config**: connection and folder details for the Grafana instance the Dashboard will use.
- **Run config**: key runtime configs to specify how job logs are to be ingested and whether the database should be rebuilt on install.
- Debug config: optional overrides used for testing and debugging only, not required for normal operation.

> [!NOTE]
> The [`config.yaml` example](configuration/examples/config.yaml) is a useful resource to see what kind of scripts configuration values the GA Dashboard expects.

> [!NOTE]
> Its best to keep `fixed_params_file` and `db_script` set to their default values from the [`config.yaml` example](configuration/examples/config.yaml) — don't change them unless you know what you're doing.

### FAQs
#### - **How to determine which `input_mode` to use?**
There are two ways to provide data to the GA Dashboard - either directly via the workload manager or through a pre-extracted file with job logs. Use `input_mode` to tell the dashboard where to pick the logs from. It currently takes two values - `file` or `sacct` (for SLURM clusters). If you want the Dashboard to pull values directly from SLURM, use `sacct`. To bypass the workload manager, you can provide a file with job logs - use `file` in this case.

> [!NOTE]
> A valid path to a job logs file must be provided through `input_log_file_path` when using `input_mode: "file"` in `config.yaml`

If you want to use a pre-extracted job logs file, use the [`run_sacct_only.py`](../scripts/slurm/run_sacct_only.py) script for SLURM clusters to generate and save one. You can run this script separately on the HPC cluster to generate the required file.

#### - **What is `skip_db_overwrite` for?**
By default (`False`), the installation script drops and recreates the database each time it runs. Set this to `True` if the database already exists and is correctly configured, and you just need to re-run the install script without losing existing data. **If you're running the Dashboard in a Docker container, this must be set to `True`**, otherwise the database will be deleted and recreated every time the container restarts.

#### - **Where do I find my `pg_version`?**
This is the version of PostgreSQL installed on the machine hosting your database. Run `psql --version` or `postgres --version` on the database host to check. This should be filled in *after* PostgreSQL is installed, not before.

#### - **What is `dashboard_folder_name` and `name` under Grafana config?**
`dashboard_folder_name` is the folder the Dashboard's panels will be organised under in the Grafana UI. `name` is the identifier Grafana uses internally for the PostgreSQL data source it creates — you generally don't need to change this unless it conflicts with an existing data source name.

#### - **Can I leave `db_name` and `dashboard_folder_name` as their defaults?**
Yes, `db_name: "ga_db"` and `dashboard_folder_name: "Green Algorithms"` are sensible defaults and only need changing if they clash with existing resources on your system.

## Cluster information ([cluster_info.yaml](templates/cluster_info.yaml))
This file contains key information about the cluster including it's workload manager, PUE (power usage effectiveness), postcode, and hardware details.

It is important that the cluster configurations represent the clusters accurately to allow for correct energy and GHG emissions estimations. 

> [!NOTE]
> The [`cluster_info.yaml` example](`configuration/examples/cluster_info__demo.yaml`) is a useful resource to see what kind of cluster configuration values the GA Dashboard expects.

### FAQs

#### - What's TDP and where can I find it?
Thermal design power or TDP refers to the maximum thermal power dissipation of a processor (CPU or GPU) under normal operating workloads. This value is generally specified by the manufacturer of the processor. The GA dashboard expects you to provide the TDP for each professor in the following manner:
- TDP per core for CPUs
- TDP for entire processor for GPUs

Once you're aware of the hardware in use, TDP values for each hardware profile can be fetched directly from the manufacturer's website/datasheets. You may also check if the value you are looking for is present [here](https://github.com/Cambridge-Sustainable-Computing-Lab/Green-Algorithms-data/blob/main/v3.1/hardware-impacts.csv).

#### - Homogenous vs heterogenous partitions?
The code needs to know what hardware is being used to estimate energy usage. Partitions where all nodes have the same hardware (and hardware profile) are considered homogenous, in this case partitions are used to map jobs to hardware. Partitions that have different hardware for different nodes (what we call here "heterogenous partitions) require node-level mapping and for these, a node list must be configured to identify what hardware profile is used by each node.

Configuring a homogenous partition `yew` in `cluster_info.yaml` (assuming a hardware profile called 'HP1'):

```yaml
yew:
    homogenous: True
    hardware_profile: HP1

```

Configuring a heterogenous partition `yew` in `cluster_info.yaml` (assuming hardware profiles 'HP1' and 'HP2'):

```yaml
yew:
    homogenous: False
    node_list:
        - hardware_profile: HP1
          range: range1-[100-200]
        - hardware_profile: HP2
          range: range2-[450-500]
```       

#### - How to find my data centre's carbon intensity?
Carbon intensity varies over time depending on the share of low-carbon energy source in the power grid. If the data centre is UK based, Green Algorithms Dashboard can use the [Carbon Intensity API](https://carbonintensity.org.uk) to dynamically fetch carbon intensity based on the `postcode` provided in `cluster_info.yaml`.

A static `CI` value must be provided in `cluster_info.yaml` for non-UK based clusters. The average carbon intensity in the data centre's location can be found [here](https://app.electricitymaps.com)


## Dashboard Users ([user_list.csv](configuration/templates/user_list.csv))

The users file should be a comma-separated file combining these columns:
* **User name**: Company/Institute user name (e.g. tg1)
* **User unique identifier (UID)**: Numeric user unique identifier (e.g. 11111)
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

> [!IMPORTANT]
> Passwords must not contain a comma character (`','`), as this will break CSV parsing.