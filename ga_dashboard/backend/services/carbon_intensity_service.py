# ------------------------------------------------------------------
# Carbon Intensity Service (add carbon intensity related code here)
# Carbon emission calculated here! 
# ------------------------------------------------------------------

from datetime import datetime, time, timedelta

from ga_dashboard.backend.services.api_service import APIService
import pandas as pd

class JobEmissionRecord:
    def __init__(self, date, energy_per_hr: float, hours_of_work: float, carbon_intensity: float):
        self.date = date
        self.energy = energy_per_hr * hours_of_work
        self.hours_of_work = hours_of_work
        self.carbon_intensity = carbon_intensity

    @staticmethod
    def calc_carbon_emission(records: list['JobEmissionRecord'], energy_per_hr: float) -> float:
        """
        Calculate the total carbon emission for a job across multiple daily records.
        Formula: (tot_job_energy / total_duration) * sum(hours_of_work_n * CI_n)
        here (tot_job_energy / total_duration) = energy_per_hr
        so, carbon emission = energy_per_hr * sum(hours_of_work_n * CI_n)

        :param records: list of JobEmissionRecord objects for the same job
        :return: carbon emission in gCO2
        """
        if not records:
            print("calc_carbon_emission(): No records provided.")
            return 0.0

        weighted_CI = sum(r.hours_of_work * r.carbon_intensity for r in records if r.carbon_intensity is not None)

        return energy_per_hr * weighted_CI

class CarbonIntensityService:
    def __init__(self, postcode: str, base_url: str ="https://api.carbonintensity.org.uk/regional/intensity/", api_key: str = None):
        self.api_service = APIService(base_url, api_key)
        self.postcode = postcode
        # self.daily_avg_CI = None

    def fetch_CI_data(self, from_date: datetime, to_date: datetime) -> list:
        """
        Fetch CI data in chunks of 7 days. Each chunk is fetched with a single API call. 
        
        :param from_date: start datetime
        :param to_date: end datetime
        :return: list of CI data points (30-min interval) between from_date and to_date for the cluster's postcode region
        """
        if not self.postcode:
            print("Postcode not found. Cannot fetch CI data.")
            return []

        all_data = []
        chunk_start = from_date

        try: 
            # Get CI data in 7-day chunks to avoid API limits
            while chunk_start < to_date:
                chunk_end = min(chunk_start + timedelta(days=7), to_date)

                # Formatting as 2026-02-20T00:00Z
                start_str = chunk_start.replace(hour=0, minute=0).strftime('%Y-%m-%dT%H:%MZ')
                end_str   = chunk_end.replace(hour=23, minute=59).strftime('%Y-%m-%dT%H:%MZ')

                endpoint = f'{start_str}/{end_str}/postcode/{self.postcode}'

                response = self.api_service.get(endpoint=endpoint, params={})

                if not response or 'data' not in response:
                    print(f"fetch_CI_data(): Failed to fetch CI data for {start_str} to {end_str}.")
                else:
                    all_data.extend(response['data']['data'])

                chunk_start = chunk_end

            return all_data
        
        except Exception as e:
            print(f"Exception occurred while fetching CI data: {e}.")
            return []

    def calc_day_average_CI(self, from_date: datetime, to_date: datetime) -> dict:
        """
        Fetch 30-min interval CI data and average per day.
        :param from_date: start datetime
        :param to_date: end datetime
        """
        raw_data = self.fetch_CI_data(from_date, to_date) # API Call

        if not raw_data:
            print("No CI data available. Cannot calculate daily average CI. Falling back to default CI from cluster info.")
            return {}

        df = pd.DataFrame(raw_data)

        df['intensity_value'] = df['intensity'].apply(
            lambda x: x.get('actual') or x.get('forecast')  # fallback to forecast if actual is missing
        )
        df['date'] = pd.to_datetime(df['from']).dt.date

        # Average CI per day
        daily_avg = (df.groupby('date')['intensity_value'].mean().round(1).reset_index())
        return {row['date'].strftime('%d-%m-%Y'): row['intensity_value'] for _, row in daily_avg.iterrows()}
    
