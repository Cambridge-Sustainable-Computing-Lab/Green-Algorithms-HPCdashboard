# ------------------------------------------------------------------
# This service class defines methods to fetch carbon intensity using an API and 
# perform required processing steps to prepare CI data to be used for further calculations.
# ------------------------------------------------------------------

import pandas as pd
from datetime import datetime, timedelta
from Green_Algorithms_core.src.ga_core.computation.carbon_intensity.ci_store import CIStorageBackend
from Green_Algorithms_core.src.ga_core.utils.api_service import APIService
from Green_Algorithms_core.src.ga_core.utils import utils

class CarbonIntensityService:
    """
    Fetches, processes, and stores daily average carbon intensity (CI) data for a given postcode region.

    NOTE: fetch_CI_data() is designed for the UK Carbon Intensity API. To support a different API, subclass this and override fetch_CI_data().
    """
    def __init__(self, postcode: str, ci_store: CIStorageBackend = None, base_url: str ="https://api.carbonintensity.org.uk/regional/intensity/", api_key: str = None):
        """
        :param postcode: UK postcode 
        :param ci_store: CI data storage backend
        :param base_url: Base URL for the carbon intensity API
        :param api_key: Optional API key. Not required for the UK Carbon Intensity API.
        """
        self.api_service = APIService(base_url, api_key)
        self.source = base_url.split('/')[2]
        self.postcode = postcode
        self.ci_store = ci_store

    def fetch_CI_data(self, from_date: datetime, to_date: datetime) -> pd.DataFrame:
        """
        Fetch CI data in chunks of 13 days. Each chunk is fetched with a single API call. 

        This is 'api.carbonintensity.org.uk' specific, to adapt for a different API, update the endpoint format, chunk size, and response parsing.
        
        :param from_date: start datetime
        :param to_date: end datetime
        :return: list of CI data points (30-min interval) between from_date and to_date for the cluster's postcode region
        """
        if not self.postcode:
            raise ValueError("Postcode not found. Cannot fetch CI data.")
        
        all_data = []

        try: 
            # Get CI data in 13-day chunks to avoid API limits (CI API limit is 14)
            chunk_start = from_date
            while chunk_start <= to_date:
                chunk_end = min(chunk_start + timedelta(days=13), to_date)

                # Formatting as 2026-02-20T00:00Z
                start_str = chunk_start.replace(hour=0, minute=0).strftime('%Y-%m-%dT%H:%MZ')
                end_str   = chunk_end.replace(hour=23, minute=59).strftime('%Y-%m-%dT%H:%MZ')

                endpoint = f'{start_str}/{end_str}/postcode/{self.postcode}'

                response = self.api_service.get(endpoint=endpoint, params={})
                # Find example of response at https://carbon-intensity.github.io/api-definitions/#get-regional-intensity-from-to

                if not response or 'data' not in response:
                    print(f"fetch_CI_data(): Failed to fetch CI data for {start_str} to {end_str}.")
                else:
                    all_data.extend(response['data']['data'])

                chunk_start = chunk_end + timedelta(days=1)
        
        except Exception as e:
            print(f"Error occurred while calling CarbonIntenistyAPI: {e}")
            return pd.DataFrame()
        
        if not all_data:
            return pd.DataFrame()
        
        ci_df = pd.DataFrame(all_data)
        ci_df['intensity_value'] = ci_df['intensity'].apply(
            lambda x: x.get('forecast') # Regional carbon intensity API provides CI as forecast
        )
        ci_df['date'] = pd.to_datetime(ci_df['from']).dt.date ## NOTE: Works for now but if we need the 30 mins intervals then this must be changed

        return ci_df[['date','intensity_value']]
    
    def calc_day_average_CI(self, from_date: datetime, to_date: datetime) -> dict:
        """
        Returns daily average CI values for the given date range, pulling from DB where
        available and falling back to the API for any missing dates.

        :param from_date: start datetime
        :param to_date: end datetime
        :return: dict mapping date strings (DD-MM-YYYY) to daily average CI values (gCO₂/kWh)
        """
        dates_list = [
                (from_date + timedelta(days=i)).strftime("%Y-%m-%d")
                for i in range((to_date.date() - from_date.date()).days + 1)
            ]
        
        ci_from_store = pd.DataFrame()
        ci_data_from_api = pd.DataFrame()

        try:
            if self.ci_store:
                ci_from_store = self.ci_store.fetch(dates_list)
                if not ci_from_store.empty:
                    stored_dates = set(ci_from_store['ci_date'].astype(str))
                    dates_list = sorted(set(dates_list) - stored_dates)

            # Find CI for remaining dates from API         
            if dates_list :
                # Fetch data from API 
                ci_data_from_api = self.fetch_CI_data(    
                    datetime.strptime(min(dates_list), "%Y-%m-%d"),
                    datetime.strptime(max(dates_list), "%Y-%m-%d")
                    )
                if not ci_data_from_api.empty:
                    # Average CI per day
                    ci_data_from_api = (ci_data_from_api.groupby('date')['intensity_value'].mean().round(1).reset_index())
                    ci_data_from_api = ci_data_from_api.rename(columns={'date': 'ci_date', 'intensity_value': 'ci_day_avg'})

                    if self.ci_store:
                        today = datetime.now().strftime("%Y-%m-%d")
                        to_store = ci_data_from_api[ci_data_from_api['ci_date'].astype(str) != today] # Skipping today's date to avoid storing unfinalised CI data, since the day hasn't ended
                        if not to_store.empty:
                            self.ci_store.save(to_store, self.source)
            
            daily_avg = utils.concat_dataframes([ci_from_store, ci_data_from_api])

            daily_avg['ci_date'] = pd.to_datetime(daily_avg['ci_date']).dt.strftime('%d-%m-%Y')
            return dict(zip(daily_avg['ci_date'], daily_avg['ci_day_avg']))
    
        except Exception as e:
            print(f"calc_day_average_CI(): Error fetching CI data: {e}")
            return {}
    




    
