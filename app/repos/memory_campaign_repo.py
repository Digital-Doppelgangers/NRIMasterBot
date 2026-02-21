from __future__ import annotations
from typing import Dict, List, Optional, Sequence
from app.domain.models import Campaign

class InMemoryCampaignRepo:
    def __init__(self) -> None:
        self._next_id: int = 1
        self._campaigns_by_user: Dict[int, List[Campaign]] = {}
        self._current_by_user: Dict[int, int] = {}  # user_id -> campaign_id

    async def create(self, user_id: int, title: str, description: str = "") -> Campaign:
        camp = Campaign(
            id=self._next_id,
            user_id=user_id,
            title=title.strip(),
            description=description.strip(),
        )
        self._next_id += 1
        self._campaigns_by_user.setdefault(user_id, []).append(camp)
        #сразу сделать текущей
        self._current_by_user[user_id] = camp.id
        return camp

    async def list(self, user_id: int) -> Sequence[Campaign]:
        return list(self._campaigns_by_user.get(user_id, []))

    async def get(self, user_id: int, campaign_id: int) -> Optional[Campaign]:
        for c in self._campaigns_by_user.get(user_id, []):
            if c.id == campaign_id:
                return c
        return None

    async def set_current(self, user_id: int, campaign_id: int) -> None:
        camp = await self.get(user_id, campaign_id)
        if camp is None:
            raise ValueError("Campaign not found")
        self._current_by_user[user_id] = campaign_id

    async def get_current(self, user_id: int) -> Optional[Campaign]:
        cid = self._current_by_user.get(user_id)
        if cid is None:
            return None
        return await self.get(user_id, cid)