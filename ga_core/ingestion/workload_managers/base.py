## This file must contain the Abstract base class that all workload managers must inherit from.
## The intention is to have an abstract class that defines the functions each workload manager must implement, e.g. pull_logs(), clean_logs(), etc.

from abc import ABC, abstractmethod
import pandas as pd

class BaseWorkloadManager(ABC):
    """
    Abstract base class for workload managers. All workload managers must inherit from this class and implement the abstract methods.
    """

    @abstractmethod
    def pull_logs(self) -> pd.DataFrame:
        """
        Pull logs from the source and return them as a pandas DataFrame.
        """
        pass

    @abstractmethod
    def clean_logs(self, logs: pd.DataFrame) -> pd.DataFrame:
        """
        Clean the logs and return the cleaned DataFrame.
        """
        pass