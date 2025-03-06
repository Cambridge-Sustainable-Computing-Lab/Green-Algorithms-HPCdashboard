Explanation of test files
--------------------

These are anonymised test files to use for debugging and development. Their main function is to bypass parts of the code, for example to be able to run it offline, or to simulate multiple users without admin access. 

The two files that are most relevant are:
- To run the code offline on a single user, use `--useCustomLogs sacct_output_single_user.txt`
- To run the code on multiple users (either offline or without admin rights), use `--use_mock_agg_data`, which will use `df_agg_X_mockMultiUsers_1.csv`.
- To run only the database generation (and possibly frontend), bypassing the backend, use `userDaily_mockMultiUsers_1.csv`.

The other files can mostly be ignored (although can occasionally be useful for debugging).

Here is a detailed description of the different files:
- `sacct_output_single_user.txt`: example output from running the HPC `sacct` command for a single user.
- `df_agg_X_mockMultiUsers_1.csv`: this is a simulated output of the `extract_data` function for multiple users (i.e. SLURM output that has been (1) converted to a dataframe, and (2) cleaned). 1 row per job.
- `df_agg_X_mockMultiUsers_2.csv`: this is a simulated output of the `enrich data` function for multiple users (i.e. SLURM output that has been (1) converted to a dataframe, (2) cleaned, and (3) enriched with energy/carbon/context metrics). 1 row per job.
- `userDaily_mockMultiUsers_1.csv`: this is the same as `df_agg_X_mockMultiUsers_2.csv`, but aggregated to have 1 row per day and per user.

To generate these test files, example data files have also been used, in particular `users_list.csv` and `cluster_info.yaml` which have simply been adapted to the names/partitions etc. of the example files above.



