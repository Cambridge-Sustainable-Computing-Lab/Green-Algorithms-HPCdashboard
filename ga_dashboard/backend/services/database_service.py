# ------------------------------------------------------------------
# Database reader/writer service (add database interaction code here)
# ------------------------------------------------------------------

import logging
import psycopg
import pandas as pd
from dataclasses import dataclass
from psycopg import sql

logger = logging.getLogger(__name__)

@dataclass
class DBSettings:
    """
    Holds database connection parameters.
    """
    db_name: str
    user: str
    password: str
    host: str
    port: int = 5432  # PostgreSQL default

class DatabaseService:
    """
    A reusable database helper for PostgreSQL operations via psycopg.
    Handles connection management and generic inserts with configurable conflict resolution.
    """

    def __init__(self, db_params: DBSettings) -> None:
        self.db_name = db_params.db_name
        self.user = db_params.user
        self.password = db_params.password
        self.host = db_params.host
        self.port = db_params.port
        self._conn = None

    # Connection management
    def connect(self) -> bool:
        """Open a connection to the database. Returns True on success."""
        try:
            self._conn = psycopg.connect(
                dbname=self.db_name,
                user=self.user,

                password=self.password,
                host=self.host,
                port=self.port,
            )
            logger.debug("Database connection established.")
            return True
        except psycopg.OperationalError as e:
            logger.error(f"Unable to connect to database: {e}")
            return False

    def disconnect(self) -> None:
        """Close the database connection if open."""
        if self._conn and not self._conn.closed:
            self._conn.close()
            logger.debug("Database connection closed.")

    def __enter__(self):
        """Support usage as a context manager: `with Database(...) as db:`"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error(f"Exception during DB operation: {exc_val}")
        self.disconnect()
        return False  # don't suppress exceptions
    
    def is_conn_ok(self):
        if not self._conn or self._conn.closed:
            return False
        return True

    def insert_data(
        self,
        table_name: str,
        columns: list[str],
        rows: list[dict],
        on_conflict: str = "DO NOTHING",
        conflict_target: list[str] | None = None,
        update_columns: list[str] | None = None,
    ) -> None:
        """
        Insert a list of row dicts into the given table.

        Args:
            table_name:       Target table, e.g. 'ga_data_aggregate'.
            columns:          Column names to insert.
            rows:             List of dicts mapping column name → value.
            on_conflict:      'DO NOTHING' or 'DO UPDATE'. Default: 'DO NOTHING'.
            conflict_target:  Columns to use in ON CONFLICT (...). Required for DO UPDATE.
            update_columns:   Columns to update on conflict. Required for DO UPDATE.

        Examples:
            # Silently skip duplicates
            db.insert_data('ga_data_aggregate', GA_COLUMNS, rows)

            # Overwrite on conflict
            db.insert_data(
                table_name='ga_user',
                columns=['user_name', 'uid', 'name', 'group_name', 'department'],
                rows=rows,
                on_conflict='DO UPDATE',
                conflict_target=['user_name'],
                update_columns=['uid', 'name', 'group_name', 'department'],
            )
        """
        if not self._conn or self._conn.closed:
            logger.error("No active database connection. Call connect() first.")
            return
        
        if not rows:
            logger.debug("No rows to insert.")
            return

        #conflict clause
        if on_conflict == "DO NOTHING":
            conflict_clause = "ON CONFLICT DO NOTHING"
        elif on_conflict == "DO UPDATE":
            if not conflict_target or not update_columns:
                raise ValueError("DO UPDATE requires both conflict_target and update_columns.")
            target = ", ".join(conflict_target)
            updates = ", ".join(f"{col} = EXCLUDED.{col}" for col in update_columns)
            conflict_clause = f"ON CONFLICT ({target}) DO UPDATE SET {updates}"
        else:
            raise ValueError(f"Unsupported on_conflict value: '{on_conflict}'. Use 'DO NOTHING' or 'DO UPDATE'.")

        col_list = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))
        sql = f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders}) {conflict_clause}"

        cur = self._conn.cursor()
        try:
            for row in rows:
                values = [row.get(col) for col in columns]
                cur.execute(sql, values)
            self._conn.commit()
            logger.debug(f"Inserted {len(rows)} rows into '{table_name}'.")
        except psycopg.DataError as e:
            logger.error(f"Data format error inserting into '{table_name}': {e}")
            self._conn.rollback()
        except Exception as e:
            logger.error(f"Unexpected error inserting into '{table_name}': {e}")
            self._conn.rollback()
        finally:
            cur.close()

    def bulk_insert_data(
        self,
        table_name: str,
        columns: list[str],
        rows: list[dict],
        on_conflict: str = "DO NOTHING",
        conflict_target: list[str] | None = None,
        update_columns: list[str] | None = None,
        batch_size: int = 1000
    ) -> None:
        """
        Bulk insert rows in batches using psycopg's executemany().
        
        Args:
            table_name: Target table.
            columns: List of column names.
            rows: List of dicts mapping column -> value.
            on_conflict: 'DO NOTHING' or 'DO UPDATE'.
            conflict_target: Required if on_conflict='DO UPDATE'.
            update_columns: Required if on_conflict='DO UPDATE'.
            batch_size: Number of rows per batch insert.
        """
        if not self._conn or self._conn.closed:
            logger.error("No active database connection. Call connect() first.")
            return

        if not rows:
            logger.debug("No rows to insert.")
            return

        # Build conflict clause
        if on_conflict == "DO NOTHING":
            conflict_clause = "ON CONFLICT DO NOTHING"
        elif on_conflict == "DO UPDATE":
            if not conflict_target or not update_columns:
                raise ValueError("DO UPDATE requires conflict_target and update_columns")
            target = ", ".join(conflict_target)
            updates = ", ".join(f"{col} = EXCLUDED.{col}" for col in update_columns)
            conflict_clause = f"ON CONFLICT ({target}) DO UPDATE SET {updates}"
        else:
            raise ValueError("Unsupported on_conflict value")

        # Build SQL with placeholders
        col_list = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))
        sql = f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders}) {conflict_clause}"

        cur = self._conn.cursor()
        try:
            # Process in batches
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i+batch_size]
                values = [tuple(row.get(col) for col in columns) for row in batch]
                cur.executemany(sql, values)
            self._conn.commit()
            logger.debug(f"Bulk inserted {len(rows)} rows into '{table_name}' in batches of {batch_size}")
        except Exception as e:
            logger.error(f"Bulk insert failed for '{table_name}': {e}")
            self._conn.rollback()
            raise
        finally:
            cur.close()

    def fetch_data(
        self,
        table_name: str,
        columns: list[str] | None = None,
        filters: dict | None = None,
    ) -> pd.DataFrame:
        """
        Fetch rows from a table, optionally filtering by column values.
        Returns results as a Pandas DataFrame.

        Args:
            table_name: Table to query, e.g. 'ga_data_aggregate'.
            columns:    Columns to select. Defaults to all ('*') if not provided.
            filters:    Dict of column → value for WHERE clauses, e.g. {'user_name': 'alice'}.
                        Multiple filters are combined with AND.

        Examples:
            # Fetch all rows and all columns
            df = db.fetch_data('ga_data_aggregate')

            # Fetch specific columns
            df = db.fetch_data('ga_data_aggregate', columns=['user_name', 'energy'])

            # Fetch with a filter
            df = db.fetch_data('ga_user', filters={'user_name': 'alice'})

            # Combine both
            df = db.fetch_data('ga_data_aggregate', columns=['user_name', 'energy'], filters={'user_name': 'alice'})
        """
        if not self._conn or self._conn.closed:
            logger.error("No active database connection. Call connect() first.")
            return pd.DataFrame()

        col_list = ", ".join(columns) if columns else "*"
        sql = f"SELECT {col_list} FROM {table_name}"

        values = []
        if filters:
            where_clauses = " AND ".join(f"{col} = %s" for col in filters)
            sql += f" WHERE {where_clauses}"
            values = list(filters.values())

        cur = self._conn.cursor()
        try:
            cur.execute(sql, values or None)
            results = cur.fetchall()
            col_names = [desc[0] for desc in cur.description]
            logger.debug(f"Fetched {len(results)} rows from '{table_name}'.")
            return pd.DataFrame(results, columns=col_names)
        except Exception as e:
            logger.error(f"Error fetching data from '{table_name}': {e}")
            return pd.DataFrame()
        finally:
            cur.close()


    def delete_by_column_values(self, table_name: str, column_name: str, values: list) -> int:
        """
        Delete rows from a table where column_name matches any value in values.
        Returns number of deleted rows.
        """
        if not self._conn or self._conn.closed:
            logger.error("No active database connection. Call connect() first.")
            return 0

        if not values:
            logger.debug("No values provided for deletion.")
            return 0

        cur = self._conn.cursor()
        try:
            query = sql.SQL("""
                DELETE FROM {table}
                WHERE {column} = ANY(%s)
            """).format(
                table=sql.Identifier(table_name),
                column=sql.Identifier(column_name),
            )
            cur.execute(query, (values,))
            deleted = cur.rowcount
            self._conn.commit()
            logger.debug(f"Deleted {deleted} rows from '{table_name}' where {column_name} in values.")
            return deleted
        except Exception as e:
            logger.error(f"Error deleting from '{table_name}': {e}")
            self._conn.rollback()
            raise
        finally:
            cur.close()