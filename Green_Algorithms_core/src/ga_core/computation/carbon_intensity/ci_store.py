# ------------------------------------------------------------------
# This file defines an abstract base class (ABC) for CI data storage backends.
# Implement this interface to add a new storage backend (e.g. database, file).
# 
# ABC docs: https://docs.python.org/3/library/abc.html
# 
# NOTE: This abstract class is defined here since it acts as an interface between the ga_core package and GA Dashboard,
# to allow for storage and retrieval of CI data to and from dashboard's database.
# ------------------------------------------------------------------
 
from abc import ABC, abstractmethod
import pandas as pd
 
class CIStorageBackend(ABC):
    """
    This is an abstract base class (ABC) that defines a common interface for saving and fetching CI data from backend storage.
    CI data can be stored to avoid repeated API calls and processing of CI data for dates that are already processed.
 
    ga_core depends only on this interface — it has no knowledge of how or where data is stored. 
    Storage implementations live in the tools that need them (e.g. GA Dashboard).
    """
 
    @abstractmethod
    def fetch(self, dates_list: list[str]) -> pd.DataFrame:
        """
        Retrieve stored daily average CI values for the given dates.
 
        :param dates_list: list of date strings in YYYY-MM-DD format
        :return: DataFrame with columns ['ci_date', 'ci_day_avg'].
                 Returns empty DataFrame if no data found.
        """
        ...
 
    @abstractmethod
    def save(self, ci_data: pd.DataFrame, source: str) -> None:
        """
        Persist daily average CI values.
 
        :param ci_data: DataFrame with columns ['ci_date', 'ci_day_avg']
        :param source: origin of the data (e.g. API base URL domain)
        """
        ... 