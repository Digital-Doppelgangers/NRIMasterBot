from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Campaign, CampaignMember, NPC, User
from db.repositories.user_repository import UserRepository


def _clean_text(value: Any, max_len: int | None = None) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    if text in {"", "-"}:
        return None

    if max_len is not None:
        return text[:max_len]

    return text


def _clean_int(value: Any) -> int | None:
    if value is None:
        return None

    text = str(value).strip()
    if text in {"", "-"}:
        return None

    try:
        return int(text)
    except (TypeError, ValueError):
        return None


class NPCRepository:
    def __init__(self) -> None:
        self.user_repository = UserRepository()

    async def create_for_user(
        self,
        session: AsyncSession,
        telegram_id: int,
        username: str | None,
        display_name: str | None,
        data: dict[str, Any],
    ) -> NPC:
        user = await self.user_repository.get_or_create_user(
            session=session,
            telegram_id=telegram_id,
            username=username,
            display_name=display_name,
        )

        npc = NPC(
            owner_user_id=user.id,
            campaign_id=user.active_campaign_id,
            name=_clean_text(data.get("name"), 128),
            role=_clean_text(data.get("role"), 64),
            description=_clean_text(data.get("description")),
            max_hp=_clean_int(data.get("max_hp")),
            current_hp=_clean_int(data.get("current_hp")),
            armor_class=_clean_int(data.get("armor_class")),
        )

        session.add(npc)
        await session.commit()
        await session.refresh(npc)
        return npc

    async def list_by_user(
        self,
        session: AsyncSession,
        telegram_id: int,
    ) -> list[NPC]:
        result = await session.execute(
            select(NPC)
            .join(User, User.id == NPC.owner_user_id)
            .where(User.telegram_id == telegram_id)
            .order_by(NPC.created_at.desc())
        )

        return list(result.scalars().all())

    async def list_by_campaign(
        self,
        session: AsyncSession,
        telegram_id: int,
        campaign_id: int,
    ) -> list[NPC]:
        result = await session.execute(
            select(NPC)
            .join(CampaignMember, CampaignMember.campaign_id == NPC.campaign_id)
            .join(User, User.id == CampaignMember.user_id)
            .where(User.telegram_id == telegram_id, NPC.campaign_id == campaign_id)
            .order_by(NPC.created_at.desc())
        )

        return list(result.scalars().all())

    async def get_user_npc(
        self,
        session: AsyncSession,
        telegram_id: int,
        npc_id: int,
    ) -> NPC | None:
        result = await session.execute(
            select(NPC)
            .join(User, User.id == NPC.owner_user_id)
            .where(User.telegram_id == telegram_id, NPC.id == npc_id)
        )

        return result.scalar_one_or_none()

    async def get_campaign_npc(
        self,
        session: AsyncSession,
        telegram_id: int,
        campaign_id: int,
        npc_id: int,
    ) -> NPC | None:
        result = await session.execute(
            select(NPC)
            .join(CampaignMember, CampaignMember.campaign_id == NPC.campaign_id)
            .join(User, User.id == CampaignMember.user_id)
            .where(
                User.telegram_id == telegram_id,
                NPC.campaign_id == campaign_id,
                NPC.id == npc_id,
            )
        )

        return result.scalar_one_or_none()

    async def _can_edit_npc(
        self,
        session: AsyncSession,
        telegram_id: int,
        npc_id: int,
    ) -> bool:
        owner_result = await session.execute(
            select(NPC)
            .join(User, User.id == NPC.owner_user_id)
            .where(User.telegram_id == telegram_id, NPC.id == npc_id)
        )
        if owner_result.scalar_one_or_none() is not None:
            return True

        admin_result = await session.execute(
            select(CampaignMember)
            .join(User, User.id == CampaignMember.user_id)
            .join(NPC, NPC.campaign_id == CampaignMember.campaign_id)
            .where(
                User.telegram_id == telegram_id,
                NPC.id == npc_id,
                CampaignMember.role.in_(("owner", "gm")),
            )
        )

        return admin_result.scalar_one_or_none() is not None

    async def update_field(
        self,
        session: AsyncSession,
        telegram_id: int,
        npc_id: int,
        field: str,
        value: str,
    ) -> NPC | None:
        if not await self._can_edit_npc(session, telegram_id, npc_id):
            return None

        npc = await session.get(NPC, npc_id)
        if npc is None:
            return None

        text_fields = {
            "name": 128,
            "role": 64,
            "description": None,
        }
        int_fields = {"max_hp", "current_hp", "armor_class"}

        if field in text_fields:
            setattr(npc, field, _clean_text(value, max_len=text_fields[field]))
        elif field in int_fields:
            setattr(npc, field, _clean_int(value))
        else:
            return None

        await session.commit()
        await session.refresh(npc)
        return npc

    async def attach_to_campaign(
        self,
        session: AsyncSession,
        telegram_id: int,
        npc_id: int,
        campaign_id: int,
    ) -> NPC | None:
        npc = await self.get_user_npc(
            session=session,
            telegram_id=telegram_id,
            npc_id=npc_id,
        )
        if npc is None:
            return None

        campaign_result = await session.execute(
            select(Campaign)
            .join(CampaignMember, Campaign.id == CampaignMember.campaign_id)
            .join(User, User.id == CampaignMember.user_id)
            .where(Campaign.id == campaign_id, User.telegram_id == telegram_id)
        )
        campaign = campaign_result.scalar_one_or_none()
        if campaign is None:
            return None

        npc.campaign_id = campaign.id
        await session.commit()
        await session.refresh(npc)
        return npc
