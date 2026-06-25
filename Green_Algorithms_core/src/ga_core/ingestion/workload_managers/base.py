## This file must contain the Abstract base class that all workload managers must inherit from.
## The intention is to have an abstract class that defines the functions each workload manager must implement, e.g. pull_logs(), clean_logs(), etc.

from abc import ABC, abstractmethod
import pandas as pd

from Green_Algorithms_core.src.ga_core.data_models.normalised_job_record import NORMALISED_SCHEMA

class BaseWorkloadManager(ABC):
    """
    Abstract base class for workload managers. All workload managers must inherit from this class and implement the abstract methods.
    This class implements a registration based factory that returns an instance of a subclass depending on the given workload manager (e.g. SLURM, PBS etc.)

    It works by registering subclasses automatically at class definition via __init__subclass__. 
    To register a subclass, pass 'manager_type' as an argument in the class signature, e.g.:

        class SlurmManager(BaseWorkloadManager, manager_type="slurm"):
            ...
        
    Registered subclasses can then be instantiated by using 'manager_type' as an identifier of the subclass like:

        manager = BaseWorkloadManager.create("slurm")
    """
    _registry: dict[str, type] = {}

    def __init_subclass__(cls, manager_type: str = None, **kwargs):
        """
        Gets called automatically by Python whenever a class inherits from BaseWorkloadManager.

        :param manager_type: string used to identify the subclass
        :param **kwargs: any additional class-level keyword arguments, forwarded to the parent via super()
        """
        if manager_type:
            BaseWorkloadManager._registry[manager_type] = cls

    @classmethod
    def create(cls, manager_type: str, **kwargs) -> "BaseWorkloadManager":
        """
        Returns the instance of the subclass indentified using 'manager_type'

        :param manager_type: string used to identify the subclass
        :param **kwargs: keyword arguments forwarded to the subclass __init__
        :return: instance of the subclass corresponding to 'manager_type'
        """
        if manager_type not in cls._registry:
            raise ValueError(f"Unknown workload manager: {manager_type!r}. Please check 'workload_manager' in your cluster configuration.")
        return cls._registry[manager_type](**kwargs)

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