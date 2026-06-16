# Data models to represent cluster information, corresponding validations, and helper methods for instantiation.

from dataclasses import dataclass, field
from typing import Optional, Dict

@dataclass
class PartitionInfo:
    """
    Data model to represent partition information and perform basic validations
    """
    name: str
    type: str
    model: str
    TDP: float

    # GPU specific
    model_CPU: Optional[str] = None
    TDP_CPU: Optional[float] = None

    # Validation
    def __post_init__(self):
        if self.TDP <= 0:
            raise ValueError(f"[cluster_info] TDP must be a positive value for partition {self.name}")
        if self.type not in ["CPU", "GPU"]:
            raise ValueError(f"[cluster_info] Type must be either 'CPU' or 'GPU' for partition {self.name}")
        if self.type == "GPU":
            if self.model_CPU is None:
                raise ValueError(f"[cluster_info] GPU partition {self.name} requires model_CPU to be specified.")
            if self.TDP_CPU is None or self.TDP_CPU <= 0:
                raise ValueError(f"[cluster_info] GPU partition {self.name} requires TDP_CPU to be a positive value.")
            
@dataclass
class EnergyCost:
    """
    Data model to represent energy cost information and perform basic validations
    """
    cost: float
    currency: str

    # Validation
    def __post_init__(self):
        if self.cost <= 0:
            raise ValueError("[cluster_info] Energy cost must be positive")

        if not self.currency:
            raise ValueError("[cluster_info] Currency cannot be empty")

@dataclass
class ClusterInfo:
    """
    Data model to represent cluster information and perform basic validations
    """
    institution: str
    cluster_name: str
    granularity_memory_request: int
    partitions: Dict[str, PartitionInfo]
    PUE: float
    CI: float
    energy_cost: EnergyCost
    postcode: Optional[str] = None

    # Optional parameters if the html output is used.
    texts_intro: Dict[str, str] = field(default_factory=dict)
    default_unit_RSS: str = "K"

    # Validation
    def __post_init__(self):
        if not self.institution:
            raise ValueError("[cluster_info] Institution cannot be empty")
        if not self.cluster_name:
            raise ValueError("[cluster_info] Cluster name cannot be empty")
        if self.granularity_memory_request <= 0:
            raise ValueError("[cluster_info] Granularity of memory request must be a positive integer")
        if self.PUE < 1:
            raise ValueError("[cluster_info] PUE must be greater than or equal to 1")
        if self.CI < 0:
            raise ValueError("[cluster_info] Carbon Intensity (CI) cannot be negative")
        if not self.partitions:
            raise ValueError("[cluster_info] At least one partition must be defined")
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'ClusterInfo':
        """
        Creates a ClusterInfo instance from a dictionary. Also handles the creation of nested PartitionInfo and EnergyCost instances.
        """
        partitions = { 
            name: PartitionInfo(name=name, **info) for name, info in data.get("partitions", {}).items() 
            }
        energy_cost = EnergyCost(**data["energy_cost"])
        
        return cls(
            institution=data["institution"],
            cluster_name=data["cluster_name"],
            granularity_memory_request=data["granularity_memory_request"],
            partitions=partitions,
            PUE=data["PUE"],
            CI=data["CI"],
            energy_cost=energy_cost,

            # Optional parameters
            postcode=data.get("postcode"),
            texts_intro=data.get("texts_intro", {}),
            default_unit_RSS=data.get("default_unit_RSS", "K")
        )
        

    
