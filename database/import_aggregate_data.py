import os
import csv
import psycopg
import argparse

"""
Import data from a CSV file into PostgreSQL.
From Laurent.
"""

def get_columns(input_file):
    with open(input_file, newline='') as csvfile:

        reader = csv.DictReader(csvfile, delimiter='\t', quotechar='"')

        dict_from_csv = dict(list(reader)[0])
 
        # making a list from the keys of the dict
        return list(dict_from_csv.keys())


def map_column_names(file_col_names):
    db_col_names = {}
    for file_col in file_col_names:
        db_col = file_col
        db_col = db_col.lower()
        if db_col in ['user','group']:
            db_col += '_name'
        db_col_names[file_col] = db_col
    return db_col_names


def get_sql_command(data,columns):
    values = []
    for col in columns:
        value = data[col]
        if type(value) == str:
            values.append(f"'{data[col]}'")
        else:
            values.append(str(data[col]))
    return ','.join(values)


def parse_string_to_number(s):
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return None


def main():

    argparser = argparse.ArgumentParser()
    argparser.add_argument("--input_file", help='Logs data', required=True, metavar='INPUT_FILE')
    argparser.add_argument("--db_name", help='Database name', required=False, metavar='DBNAME',default='ga_db')
    argparser.add_argument("--db_user", help='Database user name', required=True, metavar='DBUSER')
    argparser.add_argument("--db_password", help='Database user password', required=True, metavar='DBPASS')
    argparser.add_argument("--db_host", help='Database host', required=False, metavar='DBHOST',default='localhost')
    argparser.add_argument("--db_port", help='Database port', required=False, metavar='DBPORT',default=5432)

    args = argparser.parse_args()

    input_file = args.input_file
    db_name = args.db_name
    db_user = args.db_user
    db_password = args.db_password
    db_host = args.db_host
    db_port = args.db_port

    if not os.path.isfile(input_file):
        print("File '"+input_file+"' can't be found")
        exit(1)

    # Prepare DB column names from the ones in the input file
    raw_column_names = get_columns(input_file)
    db_column_names_mapping = map_column_names(raw_column_names)
    db_column_names = db_column_names_mapping.values()

    data = []
    print('> Parsing - start')
    with open(input_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t', quotechar='"')

        # count = 0
        for row in reader:
            data_row = {}
            for col in raw_column_names:
                db_col = db_column_names_mapping[col]
                value = row[col]
                new_value = parse_string_to_number(value)
                if new_value != None:
                    value = new_value
                if db_col in ['state_x']:
                    value = True if value == 1 else False
                data_row[db_col] = value
            values = get_sql_command(data_row,db_column_names)
            data.append(values)
    print('> Parsing - end')

    print('> DB import - start')
    # Connect to an existing database
    conn = psycopg.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port
    )
    # Open a cursor to perform database operations
    cur = conn.cursor()

    # Prepare SQL command
    sql = f"INSERT INTO ga_data_aggregate ({','.join(db_column_names)}) VALUES ({'),('.join(data)});"
    # print(sql)
    cur.execute(sql)

    # Make the changes to the database persistent
    conn.commit()

    # Close communication with the database
    cur.close()
    conn.close()
    print('> DB import - end')

if __name__ == '__main__':
    main()