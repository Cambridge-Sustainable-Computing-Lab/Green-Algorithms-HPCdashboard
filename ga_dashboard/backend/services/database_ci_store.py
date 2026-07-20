# ------------------------------------------------------------------
# Service that implements CIStore interface from GA Core for storing and fetching CI data from database
# ------------------------------------------------------------------

from datetime import datetime
from ga_core import CIStorageBackend
import pandas as pd

from ga_dashboard.backend.services.database_service import DatabaseService
from ga_dashboard.database.table_col_definitions import CARBON_INTENSITY_DATA_COLUMNS

class DatabaseCIStore(CIStorageBackend):
    """
    Implements CIStore interface (from Green_Algorithms_core package) for storing and fetching carbon intensity data from the database.
    """
    def __init__(self, db_params):
        self.db_params = db_params

    def fetch(self, dates_list) -> pd.DataFrame:
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

    def save(self, ci_data, source) -> None:
        """
        Storing the daily average CI calculated from the CI values fetched from the API

        :param ci_data: dataframe containing unique pairs of date, avg CI
        """
        today = datetime.now().strftime("%Y-%m-%d")
        ci_data = ci_data[ci_data['ci_date'].astype(str) != today] # Skipping today's date to avoid storing unfinalised CI data, since the day hasn't ended
        
        if ci_data.empty:
            return

        ci_data['source'] = [source] * ci_data.shape[0]
        with DatabaseService(self.db_params) as database:
            database.insert_data(
                table_name='carbon_intensity_data',
                rows=ci_data.to_dict(orient='records'),
                columns=CARBON_INTENSITY_DATA_COLUMNS,
           )

        