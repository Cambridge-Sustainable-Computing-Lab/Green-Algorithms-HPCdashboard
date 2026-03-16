# ------------------------------------------------------------------
# Carbon Intensity Service (add carbon intensity related code here)
# Carbon emission calculated here! 
# ------------------------------------------------------------------

import pandas as pd
from datetime import datetime, timedelta

from ga_dashboard.backend.services.api_service import APIService
from ga_dashboard.backend.services.database_service import DBSettings, DatabaseService
from ga_dashboard.database.table_col_definitions import CARBON_INTENSITY_DATA_COLUMNS

class JobEmissionRecord:
    def __init__(self, date, energy_per_hr: float, hours_of_work: float, carbon_intensity: float):
        self.date = date
        self.energy = energy_per_hr * hours_of_work
        self.hours_of_work = hours_of_work
        self.carbon_intensity = carbon_intensity

    @staticmethod
    def calc_carbon_emission(records: list['JobEmissionRecord'], energy_per_hr: float) -> float:
        """
        Calculate the total carbon emission for a job spanning multiple time periods.

        A job is split into periods (e.g. daily, hourly).
        For each period we know how long the job ran and the average CI for that period.

        Since energy consumption is assumed constant throughout the job,
        each period's emission is:
            energy_per_hr * hours_in_period * CI_of_period

        Summing across all periods gives the total carbon emission for the job.

        :param records: time period slices of the job, each with duration and CI
        :param energy_per_hr: energy consumed per hour (total_energy / total_duration)
        :return: total carbon emission in gCO2
        """
        if not records:
            print("calc_carbon_emission(): No records provided.")
            return 0.0

        weighted_CI = sum(r.hours_of_work * r.carbon_intensity for r in records if r.carbon_intensity is not None)

        return energy_per_hr * weighted_CI

class CarbonIntensityService:
    def __init__(self, postcode: str, db_params: DBSettings, base_url: str ="https://api.carbonintensity.org.uk/regional/intensity/", api_key: str = None):
        self.api_service = APIService(base_url, api_key)
        self.source = base_url.split('/')[2]
        self.postcode = postcode
        self.db_params = db_params

    def fetch_CI_data(self, from_date: datetime, to_date: datetime) -> pd.DataFrame:
        """
        Fetch CI data in chunks of 7 days. Each chunk is fetched with a single API call. 
        
        :param from_date: start datetime
        :param to_date: end datetime
        :return: list of CI data points (30-min interval) between from_date and to_date for the cluster's postcode region
        """
        all_data = []
 
        if not self.postcode:
            raise ValueError("Postcode not found. Cannot fetch CI data.")

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
    
    def store_average_CI_in_db(self, ci_data: pd.DataFrame):
        """
        Storing the daily average CI calculated from the CI values fetched from the API
        :param ci_data: dataframe containing unique pairs of date, avg CI
        """
        today = datetime.now().strftime("%Y-%m-%d")
        ci_data = ci_data[ci_data['ci_date'].astype(str) != today] # Skipping today's date to avoid storing unfinalised CI data, since the day hasn't ended
        
        if ci_data.empty:
            return

        ci_data['source'] = [self.source] * ci_data.shape[0]
        with DatabaseService(self.db_params) as database:
            database.insert_data(
                table_name='carbon_intensity_data',
                rows=ci_data.to_dict(orient='records'),
                columns=CARBON_INTENSITY_DATA_COLUMNS,
            )

    def fetch_stored_average_CI(self, dates_list: list[datetime]) -> pd.DataFrame:
        """
        Fetch stored daily average CI values from DB
        :param dates_list: list of dates
        """
        ci_data = pd.DataFrame()
        try:
            with DatabaseService(self.db_params) as database:
                    ci_data = database.fetch_data(
                        table_name='carbon_intensity_data',
                        columns=['ci_date', 'ci_day_avg'],
                        filters={'ci_date': dates_list}
                    )
        except Exception as e:
            print("Error fetching data from DB", e)
            
        return ci_data

    def calc_day_average_CI(self, from_date: datetime, to_date: datetime) -> dict:
        """
        Fetch 30-min interval CI data and average per day.
        :param from_date: start datetime
        :param to_date: end datetime
        """
        dates_list = [
                (from_date + timedelta(days=i)).strftime("%Y-%m-%d")
                for i in range((to_date.date() - from_date.date()).days + 1)
            ]
        
        ci_data_from_db = pd.DataFrame()
        ci_data_from_api = pd.DataFrame()

        try:
            # Trying to pick previously saved data from DB
            ci_data_from_db = self.fetch_stored_average_CI(dates_list)

            # Find dates for which data is not available in the DB
            if not ci_data_from_db.empty:
                db_dates = set(ci_data_from_db["ci_date"])
                dates_list = sorted(set(dates_list) - db_dates)
                
            if dates_list :
                # Fetch data from API (for missing dates)
                ci_data_from_api = self.fetch_CI_data(    
                    datetime.strptime(min(dates_list), "%Y-%m-%d"),
                    datetime.strptime(max(dates_list), "%Y-%m-%d")
                    )
                if not ci_data_from_api.empty:
                    # Average CI per day
                    ci_data_from_api = (ci_data_from_api.groupby('date')['intensity_value'].mean().round(1).reset_index())
                    ci_data_from_api = ci_data_from_api.rename(columns={'date': 'ci_date', 'intensity_value': 'ci_day_avg'})
                    self.store_average_CI_in_db(ci_data_from_api)
            
            daily_avg = pd.concat([ci_data_from_db, ci_data_from_api]).reset_index(drop=True)
            daily_avg['ci_date'] = pd.to_datetime(daily_avg['ci_date']).dt.strftime('%d-%m-%Y')
            return dict(zip(daily_avg['ci_date'], daily_avg['ci_day_avg']))
    
        except Exception as e:
            print("Error fetching data", e)
            return {}

    
