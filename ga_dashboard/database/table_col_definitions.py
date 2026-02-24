# ------------------------------------------------------------------
# Column definitions (add new tables here)
# ------------------------------------------------------------------

GA_DATA_AGGREGATE_COLUMNS = [
    'user_name', 'submitdate', 'n_jobs', 'first_job_period', 'last_job_period',
    'energy', 'energy_cpus', 'energy_gpus', 'energy_memory',
    'carbonfootprint', 'carbonfootprint_memoryneededonly', 'carbonfootprint_failedjobs',
    'cputime', 'gputime', 'wallclocktime',
    'cpuhourscharged', 'gpuhourscharged', 'memoryrequested', 'memoryoverallocationfactor',
    'n_success', 'treemonths', 'treemonths_memoryneededonly', 'treemonths_failedjobs',
    'driving', 'flying_ny_sf', 'flying_par_lon', 'flying_nyc_mel',
    'cost', 'cost_failedjobs', 'cost_memoryneededonly',
    'success_rate', 'failure_rate', 'share_carbonfootprint',
]

GA_USER_COLUMNS = ['user_name', 'uid', 'name', 'group_name', 'department', 'updated']

UNFINISHED_JOBS_COLUMNS = ['job_id', 'submit_date','state']