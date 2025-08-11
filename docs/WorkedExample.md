# Worked Example

The code in this repository implements Equation (1) of the paper:

L. Lannelongue, J. Grealy, and M. Inouye (2021). Green Algorithms: Quantifying the Carbon Footprint of Computation. *Advanced Science* **2021**, *8*, 2100707. https://doi.org/10.1002/advs.202100707 

## Energy consumption

Equation (1) says:

*E* = *t* (*n*<sub>c</sub> *P*<sub>c</sub> *u*<sub>c</sub> + *n*<sub>m</sub> *P*<sub>m</sub>) x *PUE* x 0.001

Hence

*E* = (*t* x *n*<sub>c</sub> *P*<sub>c</sub> *u*<sub>c</sub> x *PUE* x 0.001) + (*t* x *n*<sub>m</sub> *P*<sub>m</sub> x *PUE* x 0.001)

= Energy used by core (processor) + energy used by memory,

where 

*E* is the energy consumption (kWh)

*t* is the running time (hours)

*n*<sub>c</sub> is the number of cores

*n*<sub>m</sub> is the size of memory available (GB)

*u*<sub>c</sub> is the core usage factor (between 0 and 1)

*P*<sub>c</sub> is the power draw of a computing core (Watts)

*P*<sub>m</sub> is the power draw of memory (Watts)

*PUE* is the efficiency coefficient of the data centre.


The code aggregates all HPC jobs run by an individual on a single day. For ease of demonstration we choose a day when this individual ran only one job. This is JobID 7611224 from the sample data file `sacct_output_single_user.txt`.

The `sacct` output for this job is as follows:

```
UID|User|JobID|JobName|Submit|Elapsed|Partition|NNodes|NCPUS|TotalCPU|CPUTime|ReqMem|MaxRSS|WorkDir|State|Account|AllocTRES
11111|uid_1|7611224|somejob_P|2022-11-11T18:54:33|00:13:31|yew-himem|1|5|00:00:00|01:07:35|60150M||another/path|COMPLETED|group_1-sl2-cpu|billing=5,cpu=5,mem=60150M,node=1
```

**Note that we retain unrealistic precision for the quantities to avoid rounding errors in the calculations.**

The time, *t*, is the `wallclocktime`, `0 days 00:13:31`, which is 13.5166666666666667 minutes = 0.2252777777777778 hours.

The number of cores, *n*<sub>c</sub>, is 5.

We see that the `Partition` used was `yew-himem`. Referring to the file `cluster_info.yaml` in the `docs/templates` subdirectory, we see that the type of CPU model used was a Xeon Gold 6142, with TDP (Thermal Design Power) of 9.4 Watts per core. This is *P*<sub>c</sub>.

The core usage factor, *u*<sub>c</sub>, is unknown, and the paper suggests we set core usage to 100% of run time, i.e. *u*<sub>c</sub> = 1.

*PUE*, the efficiency coefficient of the data centre, is defined in the paper as *PUE* = *P*<sub>total</sub> / *P*<sub>compute</sub>. The ideal value is 1.0, meaning that all power supplied to the building is used by computing equipment. 

Thus: 

Energy used by core = *t* x *n*<sub>c</sub> *P*<sub>c</sub> *u*<sub>c</sub> x *PUE* x 0.001

= 0.2252777777777778 x 5 x 9.4 x *PUE* x 0.001

= 0.010588055555555557 x *PUE* kWh.

This value (0.010588055555555557) will be stored in the database as the `energy_cpus` column in the `ga_data_aggregate` table (without multiplying by *PUE*).

The value of *n*<sub>m</sub>, memory available, corresponds to the `sacct` output quantity `ReqMem`, and is 60150M = 60.150 GB.

*P*<sub>m</sub>, the power draw of the memory, is found by consulting the file `ga_dashboard/data/fixed_parameters.yaml`. This tells us that `power_memory_perGB: 0.3725` in Watts per GB.

Thus:

Energy used by memory = *t* x *n*<sub>m</sub> *P*<sub>m</sub> x *PUE* x 0.001

= 0.2252777777777778 x 60.150 x 0.3725 x *PUE* x 0.001

= 0.005047545729166667 x *PUE* kWh.

This value (0.005047545729166667) will be stored in the database as the `energy_memory` column in the `ga_data_aggregate` table (without multiplying by *PUE*).

And the total energy used is (0.010588055555555557 + 0.005047545729166667) x *PUE* = 0.015635601284722224 x *PUE* kWh.

From the cluster info file, we have *PUE* = 1.15

Therefore total energy used = 0.015635601284722224 x 1.15 = 0.017980941477430557 kWh


---

The `ga_data_aggregate` table in the PostgreSQL database storesone row per user per day, i.e., each row is the aggregate (sum) of all jobs submitted by that user on that day.

Our example was chosen to make life simple: on the date concerned, the user (`uid_1`) submitted only one job; hence, the aggregate data is the same as the data for the single job.

Let's look at the database entry:

```
ga_db=# select energy_cpus, energy_memory, energy from ga_data_aggregate where user_name = 'uid_1' and submitdate = '2022-11-11'; 
     energy_cpus      |    energy_memory     |        energy        
----------------------+----------------------+----------------------
 0.010588055555555555 | 0.005047545729166667 | 0.017980941477430557
(1 row)
```
We can see that the database has recorded the correct quantities, following Equation (1).

## Carbon footprint
From the same paper, Equation (3) is presented thus:

The carbon footprint *C* (in gCO<sub>2</sub>e) of producing a quantity of energy *E* (in kWh) from sources with a carbon intensity *CI* (in gCO<sub>2</sub>e kWh<sup>−1</sup>) is:

*C* = *E* × *CI*

Looking at the file `cluster_info.yaml` in the directory `docs/templates`, we find a value for *CI* = 231.12 gCO<sub>2</sub>e kWh<sup>−1</sup>. Hence, the carbon footprint of the energy of:
* the CPUs is 0.010588055555555555 x 231.12 = 2.4471114 ??
* the memory is 0.005047545729166667 x 231.12 = 1.166588768925 ??
* the total is 0.017980941477430557 x 231.12 = 4.15575519426375  <- OK, see DB entry below

NB total is NOT the other two quantities added together.

```
ga_db=# select carbonfootprint, carbonfootprint_memoryneededonly, carbonfootprint_failedjobs from ga_data_aggregate where user_name = 'uid_1' and submitdate = '2022-11-11';
 carbonfootprint  | carbonfootprint_memoryneededonly | carbonfootprint_failedjobs 
------------------+----------------------------------+----------------------------
 4.15575519426375 |                 4.15575519426375 |                          0
(1 row)
```

TODO what is `carbonfootprint_memoryneededonly`? And why is it the same as `carbonfootprint`?

----

```
ga_db=# select * from ga_data_aggregate where user_name = 'uid_1' and submitdate = '2022-11-11';
 user_name | submitdate | n_jobs | first_job_period | last_job_period |        energy        |     energy_cpus      | energy_gpus |    energy_memory     | carbonfootprint  | carbonfootprint_memoryneededonly | carbonfootprint_failedjobs |     cputime     |     gputime     |  wallclocktime  |  cpuhourscharged   | gpuhourscharged | memoryrequested | memoryoverallocationfactor | n_success |      treemonths      | treemonths_memoryneededonly | treemonths_failedjobs |     driving      |     flying_ny_sf      |   flying_par_lon    |   flying_nyc_mel   |        cost         | cost_failedjobs | cost_memoryneededonly | success_rate | failure_rate | share_carbonfootprint 
-----------+------------+--------+------------------+-----------------+----------------------+----------------------+-------------+----------------------+------------------+----------------------------------+----------------------------+-----------------+-----------------+-----------------+--------------------+-----------------+-----------------+----------------------------+-----------+----------------------+-----------------------------+-----------------------+------------------+-----------------------+---------------------+--------------------+---------------------+-----------------+-----------------------+--------------+--------------+-----------------------
 uid_1     | 2022-11-11 |      1 | 2022-11-11       | 2022-11-11      | 0.017980941477430557 | 0.010588055555555555 |           0 | 0.005047545729166667 | 4.15575519426375 |                 4.15575519426375 |                          0 | 0 days 01:07:35 | 0 days 00:00:00 | 0 days 00:13:31 | 1.1263888888888889 |               0 |           60.15 |                          1 |         1 | 0.004531903156230916 |        0.004531903156230916 |                     0 | 0.02374717253865 | 7.290798586427632e-06 | 8.3115103885275e-05 | 1.799028222625e-06 | 0.00611352010232639 |               0 |   0.00611352010232639 |            1 |            0 | 0.0005450485521610618
(1 row)
```
TODO edit above and keep only the columns we want.




[Back to Contents](./Contents.md)
