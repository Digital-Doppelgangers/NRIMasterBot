from typing import Protocol, Sequence, Optional
from app.domain.models import Character, Attributes
class CharacterRepo(Protocol):
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
    ) -> Character: ...

    async def list_by_campaign(self, user_id: int, campaign_id: int) -> Sequence[Character]: ...
    async def list_by_user(self, user_id: int) -> list[Character]:...
    async def get(self, user_id: int, character_id: int) -> Optional[Character]: ...
    async def delete(self, user_id: int, character_id: int) -> bool: ...