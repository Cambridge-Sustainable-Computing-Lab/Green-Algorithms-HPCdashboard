# ------------------------------------------------------------------
# Calculates contextually equivalent carbon metrics 
# e.g. number of trees needed to offset the carbon footprint, cost of electricity, equivalent distance driven.
# ------------------------------------------------------------------
import pandas as pd
from ga_core.models.cluster_info_model import ClusterInfo

class ContextMetricsCalculator:
    def __init__(self, cluster_info: ClusterInfo, fixed_params: dict):
        self.cluster_info = cluster_info
        self.fixed_params = fixed_params

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        for suffix in ['', '_memoryNeededOnly', '_failedJobs']:
            # Context metrics (part 1)
            df[f'treeMonths{suffix}'] = df[f'carbonFootprint{suffix}'] / self.fixed_params['tree_month']
            df[f'cost{suffix}'] = df[f'energy{suffix}'] * self.fixed_params['electricity_cost']

        ### Context metrics (part 2)
        df['driving'] = df.carbonFootprint / self.fixed_params['passengerCar_EU_perkm']
        df['flying_NY_SF'] = df.carbonFootprint / self.fixed_params['flight_NY_SF']
        df['flying_PAR_LON'] = df.carbonFootprint / self.fixed_params['flight_PAR_LON']
        df['flying_NYC_MEL'] = df.carbonFootprint / self.fixed_params['flight_NYC_MEL']

        return df