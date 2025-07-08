# Running the end-to-end demo

**NOTE:** In the case of conflicts between this and the `README` file on the home page, go with the latter.

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
User,UID,Name,Email,Group,Department
uid_1,11111,User_1,user1@example.com,group_1,Dept_3
uid_2,22222,User_2,user2@example.com,group_1,Dept_3
...
```
Displayed as a table:

| User  | UID   | Name   | Email            | Group   | Department |
| ----- | ------| -------|----------------- |---------|------------|
| uid_1 | 11111 | User_1 |user1@example.com | group_1 | Dept_3     |
| uid_2 | 22222 | User_2 |user2@example.com | group_1 | Dept_3     |
| ...   | ...   | ...    |...               | ...     | ...        |

The "teams" in the original dashboard version are the "Groups" in the end-to-end version.

Note: none of the example data in this file have a space character. But tests show it all works OK with names like "Thomas Greene", groups like "Weston group", and departments like "Department of Time Travel".

You will need to navigate to the "dashboards" menu on the Grafana server (in a web browser), and there select the Green Algorithms Demo dashboard.
