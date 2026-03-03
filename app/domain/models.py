from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from enum import Enum

@dataclass(slots=True)
class Campaign:
    id: int
    user_id: int
    title: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)

class Attr(str, Enum):
    STR = "STR"
    DEX = "DEX"
    CON = "CON"
    INT = "INT"
    WIS = "WIS"
    CHA = "CHA"

class DamageType(str, Enum):
    FIRE = "fire"
    COLD = "cold"
    LIGHTNING = "lightning"
    POISON = "poison"
    NECROTIC = "necrotic"
    RADIANT = "radiant"
    SLASHING = "slashing"
    PIERCING = "piercing"
    BLUDGEONING = "bludgeoning"
    PSYCHIC = "psychic"
    FORCE = "force"
    THUNDER = "thunder"
    ACID = "acid"

class Status(str, Enum):
    STUNNED = "stunned"
    CHARMED = "charmed"
    PRONE = "prone"
    FRIGHTENED = "frightened"

@dataclass(slots=True)
class Attributes:
    STR: int = 0
    DEX: int = 0
    CON: int = 0
    INT: int = 0
    WIS: int = 0
    CHA: int = 0

@dataclass(slots=True)
class Character:
    id: int
    user_id: int
    campaign_id: int
    name: str
    race: str
    clazz: str
    level: int = 1
    hp_base: int = 0
    ac_base: int = 0
    attrs: Attributes = field(default_factory=Attributes)
    backstory: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass(slots=True)
class Ability:
    id: int
    character_id: int
    name: str
    description: str = ""
    range: str = "melee" 
    damage_dice: str = ""   
    damage_type: Optional[DamageType] = None
    scales_with: Optional[Attr] = None
    status: Optional[Status] = None
    status_end_condition: str = ""

