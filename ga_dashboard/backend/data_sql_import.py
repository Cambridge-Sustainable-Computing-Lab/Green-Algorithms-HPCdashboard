import datetime
import pandas
import psycopg
from GA4HPCdashboard.ga_dashboard.backend.services.database_service import DBSettings, DatabaseService
from ga_dashboard.database.table_col_definitions import GA_DATA_AGGREGATE_COLUMNS
import ga_dashboard.backend.helpers.utils as utils

# TODO: From Laurent's PR code review: "It's good for now, but in the future it might make more sense to use the logging package, like in the grafana_ga modules."

class DataSQLImport:

    def __init__(self, dict_stats, db_params: DBSettings) -> None:
        '''
        Docstring for __init__
        
        :param self: Description
        :param dict_stats: data to be insered into the database
        :param db_params: contains 'db_name','db_user','db_password','db_host','db_port'
        :type db_params: dict
        '''
        self.dict_stats = dict_stats
        self.dict_users_data = dict_stats['userDaily']
        self.db_params = db_params

    def map_column_names(self, dict_key_names: list) -> dict:
        db_col_names = {}
        for file_col in dict_key_names:
            db_col = file_col
            db_col = db_col.lower()
            if db_col in ['user','group']:
                db_col += '_name'
            db_col_names[file_col] = db_col
        return db_col_names

    def convert_data_type(self, value, db_col_name:str) -> str|int|bool:
        new_value = value
        # Different timestamps
        if isinstance(value, datetime.date):
            new_value = str(value)
        elif isinstance(value, pandas._libs.tslibs.timestamps.Timestamp):
            new_value = str(value).split(' ')[0]
        elif isinstance(value, pandas._libs.tslibs.timedeltas.Timedelta):
            new_value = str(value)

        if isinstance(value, str):
            new_value = utils.parse_string_to_number(value)
        if db_col_name in ['state_x']:
            new_value = True if value == 1 else False
        return new_value
    
    def insert_data_into_db(self) -> None:
        raw_column_names = self.dict_users_data.columns # Pandas columns
        db_column_names_mapping = self.map_column_names(raw_column_names)

        data = []
        print('> Parsing - start')

        # Converting Datatypes for each row and column
        for index, row in self.dict_users_data.iterrows(): # Row by row
            data_row = {}
            for col in raw_column_names:  # Column by column
                db_col_name = db_column_names_mapping[col]
                value = self.convert_data_type(row[col],db_col_name)
                data_row[db_col_name] = value
                data.append(data_row)

        print('> Parsing - end')

        print('> DB insertion - start')
        with DatabaseService(self.db_params) as database:
            database.insert_data(
                table_name='ga_data_aggregate',
                columns=GA_DATA_AGGREGATE_COLUMNS,
                rows=data,
                on_conflict='DO NOTHING'
            )
        print('> DB insertion - end')

