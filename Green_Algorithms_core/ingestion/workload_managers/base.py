## This file must contain the Abstract base class that all workload managers must inherit from.
## The intention is to have an abstract class that defines the functions each workload manager must implement, e.g. pull_logs(), clean_logs(), etc.

from abc import ABC, abstractmethod
import pandas as pd

from Green_Algorithms_core.data_models.normalised_job_record import NORMALISED_SCHEMA

class BaseWorkloadManager(ABC):
    """
    Abstract base class for workload managers. All workload managers must inherit from this class and implement the abstract methods.
    """

    def extract_logs(self) -> pd.DataFrame:
        """
        Complete ingestion pipeline for workload managers: pull logs, clean/normalise and validate.
        Returns a DataFrame conforming to NormalisedJobRecord schema.
        This method is inherited by all workload managers and should not be overridden.
        """
        self.pull_logs()
        df = self.clean_logs()
        return self._validate(df)
    
    @abstractmethod
    def pull_logs(self) -> pd.DataFrame:
        """
        Pull logs from the source and return them as a pandas DataFrame.
        """
        pass

    @abstractmethod
    def clean_logs(self) -> pd.DataFrame:
        """
        Clean the logs and return the cleaned DataFrame.
        """
        pass

    def _validate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate adapter output against NormalisedJobRecord schema.
        Checks for missing columns and incorrect dtypes.
 
        :param df: DataFrame returned by to_normalised_df()
        :return: validated DataFrame, unchanged if valid
        :raises ValueError: if required columns are missing
        :raises TypeError: if column dtypes do not match schema
        """
        # Check for missing columns
        missing = set(NORMALISED_SCHEMA.keys()) - set(df.columns)
        if missing:
            raise ValueError(
                f"{self.__class__.__name__} is missing required columns: {missing}\n"
                f"Check to_normalised_df() output against NormalisedJobRecord in models/job.py"
            )
 
        # Check dtypes
        mismatched = {
            col: (df[col].dtype, expected)
            for col, expected in NORMALISED_SCHEMA.items()
            if str(df[col].dtype) != expected
        }
        if mismatched:
            details = "\n".join(
                f"  {col}: got {got}, expected {expected}"
                for col, (got, expected) in mismatched.items()
            )
            raise TypeError(
                f"{self.__class__.__name__} has columns with incorrect dtypes:\n{details}\n"
                f"Check to_normalised_df() output against NormalisedJobRecord in models/job.py"
            )
        return df