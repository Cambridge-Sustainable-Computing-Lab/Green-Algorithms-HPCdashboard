# ------------------------------------------------------------------
# Calculates some equivalences of carbon footprint to put impacts into context 
# e.g. number of trees needed to offset the carbon footprint, cost of electricity, equivalent distance driven.
# ------------------------------------------------------------------
import pandas as pd
from Green_Algorithms_core.src.ga_core.data_models.cluster_info_model import ClusterInfo

class ContextMetricsCalculator:
    def __init__(self, cluster_info: ClusterInfo, fixed_params: dict):
        self.cluster_info = cluster_info
        self.fixed_params = fixed_params

    # NOTE: The following static methods are separated from run() to allow for potenetial reuse e.g. for the calculator
    @staticmethod
    def calc_tree_months(carbon_footprint: float, tree_month: float) -> float:
        '''
        Number of tree-months needed to offset a carbon footprint (gCO2e).
        '''
        return carbon_footprint / tree_month
    
    @staticmethod
    def calc_distance_equivalent(carbon_footprint: float, emission_per_unit: float) -> float:
        '''
        Equivalent distance/trip metric (driving, flying routes) for a carbon footprint (gCO2e).
        '''
        return carbon_footprint / emission_per_unit

    @staticmethod
    def calc_cost(energy: float, electricity_cost: float) -> float:
        ''' 
        Cost of electricity for a given energy consumption (kWh) and electricity cost per kwh.
        '''
        return energy * electricity_cost
    
    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        '''
        Entry point for the context metrics calculation process for HPC jobs.
        :param df: [pd.DataFrame] the dataframe containing the cleaned job details
        :return: [pd.DataFrame] the same dataframe with the context metrics added
        '''
        for suffix in ['', '_memoryNeededOnly', '_failedJobs']:
            # Context metrics (part 1)
            df[f'treeMonths{suffix}'] = self.calc_tree_months(df[f'carbonFootprint{suffix}'], self.fixed_params['tree_month'])
            df[f'cost{suffix}'] = self.calc_cost(df[f'energy{suffix}'], self.fixed_params['electricity_cost'])

        ### Context metrics (part 2)
        df['driving'] = self.calc_distance_equivalent(df.carbonFootprint, self.fixed_params['passengerCar_EU_perkm'])
        df['flying_NY_SF'] = self.calc_distance_equivalent(df.carbonFootprint, self.fixed_params['flight_NY_SF'])
        df['flying_PAR_LON'] = self.calc_distance_equivalent(df.carbonFootprint, self.fixed_params['flight_PAR_LON'])
        df['flying_NYC_MEL'] = self.calc_distance_equivalent(df.carbonFootprint, self.fixed_params['flight_NYC_MEL'])

        return df