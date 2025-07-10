import datetime
import pandas
import psycopg
# import re

# TODO: From Laurent's PR code review: "It's good for now, but in the future it might make more sense to use the logging package, like in the grafana_ga modules."

class DataSQLImport:

    def __init__(self,dict_stats,db_name:str,db_user:str,db_password:str,db_host:str,db_port:int) -> None:
        self.dict_stats = dict_stats
        self.dict_users_data = dict_stats['userDaily']
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_port = db_port


    def map_column_names(self,dict_key_names:list) -> dict:
        db_col_names = {}
        for file_col in dict_key_names:
            db_col = file_col
            db_col = db_col.lower()
            if db_col in ['user','group']:
                db_col += '_name'
            db_col_names[file_col] = db_col
        return db_col_names


    def get_connection(self) -> psycopg.Connection:
        try:
            # Connect to an existing database
            conn = psycopg.connect(
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port
            )
        except psycopg.OperationalError as err:
            print(f'Error: Issue connecting to the database: {err}')
            conn = None
        return conn


    def get_sql_command(self,data:dict,columns:list) -> str:
        values = []
        for col in columns:
            value = data[col]
            if type(value) is str:
                values.append(f"'{data[col]}'")
            else:
                values.append(str(data[col]))
        return ','.join(values)


    def convert_data_type(self,value,db_col_name:str) -> str|int|bool:
        new_value = value
        # Different timestamps
        if type(value) is datetime.date:
            new_value = str(value)
        elif type(value) is pandas._libs.tslibs.timestamps.Timestamp:
            new_value = str(value).split(' ')[0]
        elif type(value) is pandas._libs.tslibs.timedeltas.Timedelta:
            new_value = str(value)

        if isinstance(value, str):
            new_value = parse_string_to_number(value)
        if db_col_name in ['state_x']:
            new_value = True if value == 1 else False
        return new_value


    def import_data(self) -> None:
        # Prepare DB column names from the ones in the input file
        raw_column_names = self.dict_users_data.columns # Pandas columns
        db_column_names_mapping = self.map_column_names(raw_column_names)
        #db_column_names = db_column_names_mapping.values()

        data = []
        print('> Parsing - start')
        # Row by row
        for index, row in self.dict_users_data.iterrows():
            data_row = {}
            # Column by column
            for col in raw_column_names:
                db_col_name = db_column_names_mapping[col]
                value = self.convert_data_type(row[col],db_col_name)
                data_row[db_col_name] = value
                data.append(data_row)
            #values = self.get_sql_command(data_row,db_column_names)
            #data.append(values)
        print('> Parsing - end')

        print('> DB import - start')
        conn = self.get_connection()
        
        if conn:
            # Open a cursor to perform database operations
            cur = conn.cursor()

            try:
                # Prepare SQL command

                # data is a list of dictionaries; item is one such dictionary
                # NB there are multiple, identical instances of each data item (why?). We only want the first in each. 
                for item in data:

                    # As we no longer want all columns in the data, we need to specify each one we want.
                    # See https://discuss.python.org/t/how-to-do-multi-line-f-strings/46634/6 - avoiding SQL injection attacks.
                    # and https://www.psycopg.org/psycopg3/docs/basic/params.html

                    # The correct way to pass variables in a SQL command is using the second argument of the Cursor.execute() method:
                    # SQL = "INSERT INTO authors (name) VALUES (%s)"  # Note: no quotes
                    # data = ("O'Reilly", )
                    # cur.execute(SQL, data)  # Note: no % operator
                     
                    # The columns in the ga_data_aggregate table in the ga_db database
                    columns = ['user_name', 'submitdate', 'n_jobs', 'first_job_period', 'last_job_period', 'energy', 'energy_cpus', 'energy_gpus', 'energy_memory', \
                               'carbonfootprint', 'carbonfootprint_memoryneededonly', 'carbonfootprint_failedjobs', 'cputime', 'gputime', 'wallclocktime', \
                               'cpuhourscharged', 'gpuhourscharged', 'memoryrequested', 'memoryoverallocationfactor', 'n_success', \
                               'treemonths', 'treemonths_memoryneededonly', 'treemonths_failedjobs', 'driving', 'flying_ny_sf', 'flying_par_lon', 'flying_nyc_mel',\
                               'cost', 'cost_failedjobs', 'cost_memoryneededonly', 'success_rate', 'failure_rate', 'share_carbonfootprint']

                    data = []
                    for col in columns:
                        if col in item.keys():
                            val = item[col]
                            # Check if numeric 
                            # if re.match(r'^\d+\.?\d+$', str(val)):
                            #     data.append(val)
                            # else:
                            #     data.append(f"'{val}'")
                            data.append(val)

                    num_columns = len(columns)

                    # The ON CONFLICT DO NOTHING is a temporary hack to stop the duplicate values being (attempted to be) added 
                    sql = f"INSERT INTO ga_data_aggregate ({", ".join(columns)}) VALUES("
                    sql += "%s"
                    for i in range(1, num_columns):
                        sql += ", %s"
                    sql += ") ON CONFLICT DO NOTHING"
                    #print(sql)
                    #print(data)
                    cur.execute(sql, data)

                # Make the changes to the database persistent
                conn.commit()
            except psycopg.DataError as e:
                print(f'Error: Issue with the data format to be imported: {e}')
            except Exception as e:
                print(f'Error: Issue while attempting to insert new data: {e}')

            # Close connection with the database
            cur.close()
            conn.close()
        print('> DB import - end')


def parse_string_to_number(s:str) -> int | float | str:
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s
