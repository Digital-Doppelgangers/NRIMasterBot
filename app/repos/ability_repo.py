from typing import Protocol, Sequence, Optional
from app.domain.models import Ability, DamageType, Attr,Status


class AbilityRepo(Protocol):
    async def add_to_character(
        self,
        character_id: int,
        name: str,
        range_text: str,
        description: str = "",
        damage_dice: str = "",
        damage_type: Optional[DamageType] = None,
        scales_with: Optional[Attr] = None,
        status: Optional[Status] = None,
        status_end_condition: str = ""
    ) -> Ability: ...


    async def list(self, character_id: int) -> Sequence[Ability]: ...
    async def delete(self, ability_id: int) -> bool: ...