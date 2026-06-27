# ------------------------------------------------------------------
# Contains the data model for representing emissions for a job on a specific date. 
# Used for calculating carbon emissions based on energy usage and day-to-day carbon intensity.
# ------------------------------------------------------------------

from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class JobEmissionRecord:
    """Represents a job's energy usage on a specific date."""
    date: datetime
    hours_of_work: float
    carbon_intensity: float | None
    energy: float = field(init=False) # Not passed when creating the object, but calculated in __post_init__ later
    energy_per_hr: float = field(repr=False) # Intermediate value - not included in representation of the data class

    def __post_init__(self):
        self.energy = self.energy_per_hr * self.hours_of_work