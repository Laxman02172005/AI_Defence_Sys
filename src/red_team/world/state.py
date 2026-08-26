"""World State maintaining the synthetic payment simulation."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from red_team.schemas.entities import (
    Customer,
    Account,
    Device,
    Merchant,
    Beneficiary,
    Relationship,
    Session,
)
from red_team.schemas.events import Event


class WorldState(BaseModel):
    """The authoritative state of the Normal World simulation."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    current_time: datetime
    
    customers: Dict[str, Customer] = Field(default_factory=dict)
    accounts: Dict[str, Account] = Field(default_factory=dict)
    devices: Dict[str, Device] = Field(default_factory=dict)
    merchants: Dict[str, Merchant] = Field(default_factory=dict)
    beneficiaries: Dict[str, Beneficiary] = Field(default_factory=dict)
    relationships: Dict[str, Relationship] = Field(default_factory=dict)
    
    # Active sessions keyed by customer_id
    active_sessions: Dict[str, Session] = Field(default_factory=dict)
    
    # Customer devices mapping
    customer_devices: Dict[str, List[str]] = Field(default_factory=dict)
    
    event_history: List[Event] = Field(default_factory=list)

    def advance_time(self, delta_seconds: int) -> None:
        """Advance the simulation clock."""
        from datetime import timedelta
        self.current_time += timedelta(seconds=delta_seconds)

    def append_event(self, event: Event) -> None:
        """Append an event to the chronological history."""
        self.event_history.append(event)
