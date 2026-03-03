from __future__ import annotations
from typing import Dict, List, Optional, Sequence
from app.domain.models import Character, Attributes

class InMemoryCharacterRepo:
    def __init__(self) -> None:
        self._next_id: int = 1
        self._characters_by_user: dict[int, list[Character]] = {}
    async def create(
        self,
        user_id: int,
        campaign_id: int,
        name: str,
        race: str,
        clazz: str,
        level: int = 1,
        hp_base: int = 10,
        ac_base: int = 10,
        attrs: Optional[Attributes] = None,
        backstory: str = ""
    ) -> Character:
        attrs = attrs or Attributes()
        char=Character(
            id=self._next_id,
            user_id=user_id,
            campaign_id=campaign_id,
            name=name.strip(),
            race=race.strip(),
            clazz=clazz.strip(),
            level= level,
            hp_base=hp_base,
            ac_base=ac_base,
            attrs=attrs,
            backstory=backstory.strip()
        )
        self._next_id += 1
        self._characters_by_user.setdefault(user_id, []).append(char)
        return char
    async def list_by_user(self, user_id: int) -> list[Character]:
        return list(self._characters_by_user.get(user_id, []))
    
    async def list_by_campaign(self, user_id: int, campaign_id: int) -> list[Character]:
        return [c for c in self._characters_by_user.get(user_id, []) if c.campaign_id == campaign_id]
    
    async def get(self, user_id: int, character_id: int) -> Optional[Character]:
        for c in self._characters_by_user.get(user_id, []):
            if c.id == character_id:
                return c
        return None
    async def delete(self, user_id: int, character_id: int) -> bool:
        characters = self._characters_by_user.get(user_id, [])
        for i, c in enumerate(characters):
            if c.id == character_id:
                characters.pop(i)
                if not characters:
                    self._characters_by_user.pop(user_id, None)
                return True
        return False