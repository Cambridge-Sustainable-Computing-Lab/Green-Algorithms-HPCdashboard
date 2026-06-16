# ------------------------------------------------------------------
# Abstract base class for CI data storage backends.
# Implement this interface to add a new storage backend (e.g. database, file).
# ------------------------------------------------------------------
 
from abc import ABC, abstractmethod
import pandas as pd
 
class CIStore(ABC):
    """
    Contract for CI data storage backends.
 
    ga_hpc_core depends only on this interface — it has no knowledge
    of how or where data is stored. Storage implementations live in
    the tools that need them.
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