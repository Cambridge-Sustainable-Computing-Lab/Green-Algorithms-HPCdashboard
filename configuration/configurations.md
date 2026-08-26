# Guide to using configuration templates

The two main configurations that must be set up before running the Green Algorithms Dashboard are:
1. [cluster_info.yaml](#cluster-information-cluster_infoyaml)
2. [config.yaml](#runtime-configurations-configyaml)
3. [user_list.csv](#dashboard-users-user_listcsv)

It is important to edit these and configure them to make the GA Dashboard work for your HPC cluster.

## Cluster information ([cluster_info.yaml](templates/cluster_info.yaml))
This file contains key information about the cluster including it's workload manager, PUE (power usage effectiveness), postcode, and hardware details.

It is important that the cluster configurations represent the clusters accurately to allow for correct energy and GHG emissions estimations. 

> [!NOTE]
> The [`cluster_info.yaml` example](`configuration/examples/cluster_info__demo.yaml`) is a useful resource to see what kind of cluster configuration values the GA Dashboard expects.

### FAQs
#### - Where to find hardware profiles, partitions, and node lists?
The HPC team in your institution are the best people to ask for this information.

#### - What's TDP and where can I find it?
Thermal design power or TDP refers to the maximum thermal power dissipation of a processor (CPU or GPU) under normal operating workloads. This value is generally specified by the manufacturer of the processor.

Once you're aware of the hardware in use, TDP values for each hardware profile can be fetched directly from the manufacturer's website/datasheets. You may also check if the value you are looking for is present [here](https://github.com/Cambridge-Sustainable-Computing-Lab/Green-Algorithms-data/blob/main/v3.1/hardware-impacts.csv).

#### - Homogenous vs heterogenous partitions?
Partitions where all nodes have the same hardware profile are considered homogenous, where as those that have varying hardware profiles across it's nodes are heterogenous. Since the energy consumption of a job depends on the hardware it uses, it is important to know which partition/node it ran on. For homogenous paritions this is straightforward, but in case of heterogenous partitions a node list must be configured to represent the different node ranges within each heterogenous partition that have the same hardware profile.

Configuring a homogenous parition in the cluster config. :
(assuming a hardware profile called 'HP1')

```
yew:
    homogenous: True
    hardware_profile: HP1

```

Configuring a heterogenous partition in the cluster config. :
(assuming hardware profiles 'HP1' and 'HP2')

```
yew:
    homogenous: False
    node_list:
        - range: range1-[100-200]
          hardware_profile: HP1
        - range: range2-[450-500]
          hardware_profile: HP2
```       

#### - How to find my data centre's carbon intensity?
For most locations carbon intensity varies over time depending on the 'cleanliness' of the power grid. If the data centre is UK based, Green Algorithms Dashboard can use the [Carbon Intensity API](https://carbonintensity.org.uk) to dynamically fetch carbon intensity based on the `postcode` provided in cluster config.

A static `CI` value must be provided in the cluster config for non-UK based clusters. The average carbon intensity in the data centre's location can be found [here](https://app.electricitymaps.com)

## Scripts Configuration ([config.yaml](templates/config.yaml))

This is your master configuration file. It tells the Dashboard where to find your other config files, how to connect to Grafana and PostgreSQL, and how to run. It is split into five sections:

- **Config file paths**: locations of the other files the Dashboard depends on (`cluster_info.yaml`, the user list, and the fixed parameters file).
- **Database config**: connection details for the PostgreSQL database that stores user details, processed logs data, and avg. carbon intensity values (UK only).
- **Grafana config**: connection and folder details for the Grafana instance the Dashboard will use.
- **Run config**: key runtime configs to specify how job logs are to be ingested and whether the database should be rebuilt on install.
- Debug config: optional overrides used for testing and debugging only, not required for normal operation.

> [!NOTE]
> The [`config.yaml` example](configuration/examples/config.yaml) is a useful resource to see what kind of runtime configuration values the GA Dashboard expects.

> [!NOTE]
> Its best to keep `fixed_params_file` and `db_script` set to their default values from the [`config.yaml` example](configuration/examples/config.yaml) — don't change them.

### FAQs
#### - **How to determine which `input_mode` to use?**
`input_mode` currently takes two values - `sacct` or `file`. If you want the Dashboard to pull values directly from SLURM, use `sacct`. To bypass the workload manager altogether, you can provide a logs file to the Dashboard - use `file` in this case.

If your cluster uses SLURM and you want to ingest logs via a logs file, the [`run_sacct_only.py`](../scripts/slurm/run_sacct_only.py) script should be used separately on the HPC cluster to generate the required file.

#### - **What is `skip_db_overwrite` for?**
By default (`False`), the installation script drops and recreates the database each time it runs. Set this to `True` if the database already exists and is correctly configured, and you just need to re-run the install script without losing existing data. **If you're running the Dashboard in a Docker container, this must be set to `True`**, otherwise the database will be deleted and recreated every time the container restarts.

#### - **Where do I find my `pg_version`?**
This is the version of PostgreSQL installed on the machine hosting your database. Run `psql --version` or `postgres --version` on the database host to check. This should be filled in *after* PostgreSQL is installed, not before.

#### - **What is `dashboard_folder_name` and `name` under Grafana config?**
`dashboard_folder_name` is the folder the Dashboard's panels will be organised under in the Grafana UI. `name` is the identifier Grafana uses internally for the PostgreSQL data source it creates — you generally don't need to change this unless it conflicts with an existing data source name.

#### - **Can I leave `db_name` and `dashboard_folder_name` as their defaults?**
Yes, `db_name: "ga_db"` and `dashboard_folder_name: "Green Algorithms"` are sensible defaults and only need changing if they clash with existing resources on your system.

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