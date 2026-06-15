# ------------------------------------------------------------------
# Main entry point for the Green_Algorithms_core package.
# This module defines the HPCDataProcessor class, which orchestrates the data processing pipeline:
# 1. Extracts raw logs from the workload manager (e.g. SLURM)
# 2. Enriches the data by calculating energy usage, carbon footprint, and contextual metrics.
# 3. Stores the enriched data using a CIStore implementation (Optional)
# ------------------------------------------------------------------

import pandas as pd
from Green_Algorithms_core.processing.carbon import CarbonCalculator
from Green_Algorithms_core.processing.carbon_intensity.ci_store import CIStore
from Green_Algorithms_core.processing.context_metrics import ContextMetricsCalculator
from Green_Algorithms_core.processing.energy import EnergyCalculator
from Green_Algorithms_core.data_models.cluster_info_model import ClusterInfo
from Green_Algorithms_core.ingestion.workload_managers.slurm.manager import SlurmManager
from Green_Algorithms_core.processing.carbon_intensity.carbon_intensity import CarbonIntensityService
from Green_Algorithms_core.utils import utils

class HPCDataProcessor:
    """
    Data processor class to load settings, extract, process, and store logs.
    """
    def __init__(self, config_data: dict, cluster_info: dict, fixed_params: dict, has_slurmAdmin: bool = True):
        """
        Loads cluster information, fixed parameters file, database settings, and users information using config data.
        Initialses Green Algorithms Tools (GA_tools) object - used for processing logs.

        :param config_data: dict containing configurations from config file
        :param cluster_info: dict containing cluster information
        :param fixed_params: dict containing fixed parameters
        :param users_df: pd.DataFrame containing user information
        :param has_slurmAdmin: bool indicating if slurm admin rights are available
        """

        self.cluster_info = ClusterInfo.from_dict(cluster_info)
        self.fixed_params = fixed_params
        self.has_slurmAdmin = has_slurmAdmin
        self.config_data = config_data

    # Ingestion
    def extract_data(self) -> pd.DataFrame:
        if 'use_mock_agg_data' in self.config_data.keys(): # DEBUGONLY Create/use some mock jobs with different users
            return utils.get_mock_agg_data()
        
        ### Pull usage statistics from the workload manager
        WM = SlurmManager(self.config_data, self.cluster_info)
        df_agg = WM.extract_logs()  # Pull and clean logs

        # Check if there are any jobs during the period from this directory and with these jobIDs
        utils.check_empty_results(df_agg, self.config_data)

        # Check that there is only one user's data if no admin right
        if not self.has_slurmAdmin:
            if len(set(df_agg.UserX)) > 1:
                raise ValueError(f"More than one user's logs was included, despite --slurmAdmin not used: {set(df_agg.UserX)}")

        return df_agg
    
    def enrich_data(self, df: pd.DataFrame, ci_store: CIStore = None) -> pd.DataFrame:
        """
        Adds data about the carbon footprint, etc.
        :param df: [pd.DataFrame] The existing data we've extracted.
        :param fixed_params: [dict] The fixed parameters used.
        :param GA [GA_tools] A GA_tools object. 
        :return: [pd.DataFrame] The enriched data.
        """
        ### Fetching Carbon Intensity
        postcode = self.cluster_info.postcode
        ci_avg_data = {}
        if postcode:
            postcode = postcode[:3] # Taking only the first three letters from the postcode
            ci_service = CarbonIntensityService(postcode, ci_store)
            ci_avg_data = ci_service.calc_day_average_CI(df.StartDatetimeX.min(), df.EndDatetimeX.max())
        
        ## Energy
        df = EnergyCalculator(self.cluster_info, self.fixed_params).run(df)

        ### carbon footprint
        df = CarbonCalculator(self.cluster_info, ci_avg_data).run(df)

        ## Context metrics
        df = ContextMetricsCalculator(self.cluster_info, self.fixed_params).run(df)

        return df
