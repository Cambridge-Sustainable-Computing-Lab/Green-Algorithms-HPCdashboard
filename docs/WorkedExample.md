# Worked Example

The code in this repository implements Equation (1) of the paper:

L. Lannelongue, J. Grealy, and M. Inouye (2021). Green Algorithms: Quantifying the Carbon Footprint of Computation. *Advanced Science* **2021**, *8*, 2100707. https://doi.org/10.1002/advs.202100707 

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

We see that the `Partition` used was `yew-himem`. Referring to the file `cluster_info.yaml` in the `samples` subdorectory, we see that the type of CPU model used was a Xeon Gold 6142, with TDP (Thermal Design Power) of 9.4 Watts per core. This is *P*<sub>c</sub>.

The core usage factor, *u*<sub>c</sub>, is unknwon, and the paper suggests we set core usage to 100% of run time, i.e. *u*<sub>c</sub> = 1.

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



[Back to Contents](./Contents.md)
