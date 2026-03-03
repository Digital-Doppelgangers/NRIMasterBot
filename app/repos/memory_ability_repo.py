from __future__ import annotations
from typing import Optional

from app.domain.models import Ability, DamageType, Attr, Status


class InMemoryAbilityRepo:
    def __init__(self) -> None:
        self._next_id: int = 1
        self._abilities_by_character: dict[int, list[Ability]] = {}

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
    ) -> Ability:

        ability = Ability(
            id=self._next_id,
            character_id=character_id,
            name=name.strip(),
            description=description.strip(),
            range=range_text.strip(),
            damage_dice=damage_dice.strip(),
            damage_type=damage_type,
            scales_with=scales_with,
            status=status,
            status_end_condition=status_end_condition.strip()
        )

        self._next_id += 1

        self._abilities_by_character.setdefault(character_id, []).append(ability)

        return ability

    async def list(self, character_id: int) -> list[Ability]:
        return list(self._abilities_by_character.get(character_id, []))

    async def delete(self, ability_id: int) -> bool:
        for character_id, abilities in self._abilities_by_character.items():
            for i, ability in enumerate(abilities):
                if ability.id == ability_id:
                    abilities.pop(i)

                    # подчистим пустой список
                    if not abilities:
                        self._abilities_by_character.pop(character_id, None)

                    return True

        return False