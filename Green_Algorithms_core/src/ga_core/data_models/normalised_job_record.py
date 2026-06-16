from dataclasses import dataclass
from datetime import timedelta
import pandas as pd
 
@dataclass
class NormalisedJobRecord:
    """
    For a single HPC job record.
    This is the output contract of every workload manager adapter.
    All workload manager adapters must produce a DataFrame whose columns match these field names and types exactly.
    """
    #total elapsed wall time of the job
    WallclockTimeX: timedelta

    #timestamp when the job was submitted
    SubmitDatetimeX: pd.Timestamp
    
    #timestamp when the job started
    StartDatetimeX: pd.Timestamp
 
    #timestamp when the job finished
    EndDatetimeX: pd.Timestamp
 
    # Total CPU time across all assigned CPU cores
    TotalCPUtime2useX: timedelta
    
    # Total GPU time across all assigned GPUs
    TotalGPUtime2useX: timedelta
 
    # Requested memory
    ReqMemX: float
    
    # Actual amount of memory needed by the job
    NeededMemX: float
 
    # Ratio of memory requested to memory needed
    memOverallocationFactorX: float
 
    # Total CPU core hours charged for the job
    CPUhoursChargedX: float
 
    # Total GPU hours charged for the job
    GPUhoursChargedX: float
    
    # Queue/paritition the job ran on
    PartitionX: str
 
    # Type of partition: 'CPU' or 'GPU'
    PartitionTypeX: str
    
    # Username of the job owner
    UserX: str
 
    # User id of the job owner
    UIDX: int
    
    # Standardised job's final state. 1 = success, -1 = custom success codes, 0 = failed and others
    StateX: int
 
# Column-level metadata for validation and documentation
# Maps field name -> expected pandas dtype
NORMALISED_SCHEMA: dict[str, str] = {
    "WallclockTimeX":           "timedelta64[ns]",
    "SubmitDatetimeX":          "datetime64[ns]",
    "StartDatetimeX":           "datetime64[ns]",
    "EndDatetimeX":             "datetime64[ns]",
    "TotalCPUtime2useX":        "timedelta64[ns]",
    "TotalGPUtime2useX":        "timedelta64[ns]",
    "ReqMemX":                  "float64",
    "NeededMemX":               "float64",
    "memOverallocationFactorX": "float64",
    "CPUhoursChargedX":         "float64",
    "GPUhoursChargedX":         "float64",
    "PartitionX":               "object",
    "PartitionTypeX":           "object",
    "UserX":                    "object",
    "UIDX":                     "object",
    "StateX":                   "int64",
}