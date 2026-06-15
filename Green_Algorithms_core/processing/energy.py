# ------------------------------------------------------------------
# Implements Green Algorithms energy calculation methodology
# Estimates energy consumption of HPC jobs based on their resource usage and the cluster information.
# ------------------------------------------------------------------

import numpy as np
import pandas as pd

class EnergyCalculator:
    def __init__(self, cluster_info, fixed_params):
        self.cluster_info = cluster_info
        self.fixed_params = fixed_params

    def _calculate_energies_by_row(self, row):
        '''
        Calculate the energy usage based on the job's parameters
        :param row: [pd.Series] one row of usage statistics, corresponding to one job
        :return: [pd.Series] the same statistics with the energies added
        '''
        ### CPU and GPU
        partition_info = None

        try:
            partition_info = self.cluster_info.partitions[row.PartitionX]
        except KeyError as ke:
            # Raise error if key not found.
            # TODO Make checking of all keys more robust, and explain what to do when a key is missing.
            print(f"calculate_energies(): KeyError: {ke}. Exiting...")
            exit

        if not partition_info:  #is None:
            print("calculate_energies(): partition_info is None. Exiting...")
            exit

        if row.PartitionTypeX == 'CPU':
            TDP2use4CPU = partition_info.TDP
            TDP2use4GPU = 0
        else:
            TDP2use4CPU = partition_info.TDP_CPU
            TDP2use4GPU = partition_info.TDP

        row['energy_CPUs'] = row.TotalCPUtime2useX.total_seconds() / 3600 * TDP2use4CPU / 1000  # in kWh

        row['energy_GPUs'] = row.TotalGPUtime2useX.total_seconds() / 3600 * TDP2use4GPU / 1000  # in kWh

        ### memory
        for suffix, memory2use in zip(['','_memoryNeededOnly'], [row.ReqMemX,row.NeededMemX]):
            row[f'energy_memory{suffix}'] = row.WallclockTimeX.total_seconds()/3600 * memory2use * self.fixed_params['power_memory_perGB'] /1000 # in kWh
            row[f'energy{suffix}'] = (row.energy_CPUs +  row.energy_GPUs + row[f'energy_memory{suffix}']) * self.cluster_info.PUE # in kWh

        return row
    
    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.apply(self._calculate_energies_by_row, axis=1)
        try:
            df['energy_failedJobs'] = np.where(df.StateX == 0, df.energy, 0)
        except AttributeError as err:
            print(f"enrich_data(): AttributeError: {err}")
            # TODO Explain this error, and what to do about it.
            return None  # or should we exit?
        return df