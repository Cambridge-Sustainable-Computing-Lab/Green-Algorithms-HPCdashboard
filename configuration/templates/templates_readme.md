# Guide to using configuration templates

The two main configurations that must be set up before running the Green Algorithms dashboard are:
1. [cluster_info.yaml](#cluster-information-cluster_infoyaml)
2. [config.yaml](#runtime-configurations-configyaml)

It is important to edit these and configure them to make the GA Dashboard work for your HPC cluster.

## Cluster information (cluster_info.yaml)
This file contains key information about the cluster including it's workload manager, PUE (power usage effectiveness), postcode, and hardware details.

It is important that the cluster configurations represent the clusters accurately to allow for correct energy and GHG emissions estimations. 

> !NOTE
> `configuration/examples/cluster_info__demo.yaml` is a useful worked example to see what kind of cluster configuration values the GA Dashboard expects.

### FAQs
#### - Where to find hardware profiles, partitions, and node lists?
The HPC team in your institution are the best people to ask for this information.

#### - What's TDP and where can I find it?
Thermal design power or TDP refers to the maximum thermal power dissipation of a processor (CPU or GPU) under normal operating workloads. This value is generally specified by the manufacturer of the processor.

Once you're aware of the hardware in use, TDP values for each hardware profile can be fetched directly from the manufacturer's website. You may also check if the value you are looking for is present [here](https://github.com/Cambridge-Sustainable-Computing-Lab/Green-Algorithms-data/blob/main/v3.1/hardware-impacts.csv).

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

## Runtime Configurations (config.yaml)

This is your master configuration that contains paths to other configurations (like `cluster_info.yaml`), Grafana and PostgreSQL database configurations, and runtime instructions.

