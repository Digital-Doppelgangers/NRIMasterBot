from dataclasses import dataclass, field
from datetime import datetime

@dataclass(slots=True)
class Campaign:
    id: int
    user_id: int
    title: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)