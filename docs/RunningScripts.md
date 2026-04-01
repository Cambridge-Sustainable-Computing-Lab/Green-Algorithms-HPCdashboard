
# Scripts: Running and Managing GA4HPCdashboard

The directory - `scripts/` - contains the executable scripts used to install, configure, and operate the Green Algorithms for HPC (GA4HPCdashboard) system. These scripts are designed to be run in a largely non-interactive manner, driven primarily by configuration files, and command line arguments. These are intended for HPC administrators or platform teams.

---
## Overview

The GA4HPCdashboard system consists of three main components:

1. **Backend** – extracts HPC usage data (via SLURM `sacct`), enriches it with energy usage and carbon footprint information, aggregates it per user per day, and stores it in a database.
2. **Database** – a PostgreSQL database that stores enriched and aggregated usage data.
3. **Frontend** – Grafana dashboards that query the database and present usage and sustainability metrics.

The scripts in this directory support:
- Initial installation and configuration of the database and Grafana
- One-off historical data ingestion
- Ongoing scheduled data ingestion (e.g. via `cron`)

## Configuration model

All scripts are driven by a **YAML configuration file** passed via the `--config` argument.

You must prepare the following files before running any scripts:

- **Scripts configuration file** (YAML)
  - Copy from `configuration/templates/config.yaml`
  - Defines database connection parameters, paths to other configuration files, and runtime options
- **Cluster configuration file** (YAML)
  - Copy from `configuration/templates/cluster_info.yaml`
  - Describes HPC hardware (CPU/GPU models, TDP, PUE, etc.)
- **Dashboard users file** (CSV)
  - Copy from `configuration/templates/user_list.csv`
 - Lists all users to be created in the database and Grafana (these are the users of the HPC).
- **Fixed parameters file** (YAML)
  - Example: `ga_dashboard/data/fixed_parameters.yaml`

> !Note
> Sensitive values such as **database and Grafana passwords must not be stored in configuration files**. They are provided interactively or via secure command-line mechanisms when required.

---
## Installation and initial setup

### Install the dashboard

To perform a full installation (database creation, user import, and Grafana setup), run:

```
python scripts/install_GAdashboard.py --config <your_config_file.yaml>
```

This script will:
- Create an empty PostgreSQL database
- Insert dashboard users into the database
- Configure Grafana:
  - Create the PostgreSQL data source
  - Import dashboards into a dedicated folder
  - Create Grafana users
  - Set folder permissions

If not passed as arguments, you may be prompted for:
- PostgreSQL admin password
- Grafana admin password

> ⚠️ This script will overwrite existing dashboard-related resources if re-run with the same configuration.
> set `skip_db_overwrite : True` in `config.yaml` to skip this in case database is already configured.

---
## HPC usage data ingestion

### One-off historical ingestion

To ingest all available historical SLURM logs (or a configured date range), run:

```
python scripts/run_green_algorithms_on_historical_logs.py --config <your_config_file.yaml>
```

This script:
- Runs `sacct` (unless custom logs are configured)
- Ingests data using `sacct` in batches (use `--batch_size` to define number of days per batch)
- Enriches usage data with carbon footprint metrics
- Aggregates data to one row per user per day
- Writes results to the PostgreSQL database

If no `startDay` / `endDay` are defined in the configuration file, all available logs are processed.

---
### Scheduled / recurring ingestion

For regular updates (e.g. daily via `cron`), use:

```
python scripts/run_green_algorithms_on_logs.py --config <your_config_file.yaml>
```

By default, this processes logs from the previous day unless overridden in the configuration file.

---
## Notes on `sacct` execution

- The default workflow assumes the scripts are run on a system with access to SLURM and the `sacct` command.
- All logs are currently loaded into memory before being written to the database.
  - This has been tested successfully with up to ~1 million jobs.
  - One off historical ingestion is performed in batches (use `--batch_size` to configure number of days per batch).
  - Future versions may also include batching of daily jobs for improved scalability.

If your architecture requires separating log extraction and database ingestion (e.g. different machines), this is not yet fully automated in the Gamma version. Contact the maintainers for guidance.

---
## Grafana

Grafana must be installed and running separately.

Once the Grafana server is running (default: http://localhost:3000), users created during installation can log in and access the **Green Algorithms** dashboards.

By default:
- Admin user: `admin`
- You should change the admin password immediately after installation

---
## Help and troubleshooting

All scripts support the `--help` flag for detailed argument descriptions.

If you encounter issues related to:
- Database connectivity
- Grafana configuration
- SLURM log ingestion

Ensure that:
- Paths in the configuration file are absolute
- Required services (PostgreSQL, Grafana) are running
- User lists and cluster configuration files are valid and complete


[Back to Contents](./Contents.md)
