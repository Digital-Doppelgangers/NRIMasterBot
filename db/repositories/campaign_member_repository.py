from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import CampaignMember, User
# 	enum('owner', 'gm', 'player', 'viewer') 	

class CampaignMemberRepository:
    async def add_member(
        self,
        session: AsyncSession,
        campaign_id: int,
        user_id: int,
        role: str = "player",
    ) -> CampaignMember:
        member = CampaignMember(
            campaign_id=campaign_id,
            user_id=user_id,
            role=role,
        )

        session.add(member)
        await session.flush()

        return member

    async def get_member(
        self,
        session: AsyncSession,
        campaign_id: int,
        user_id: int,
    ) -> CampaignMember | None:
        result = await session.execute(
            select(CampaignMember).where(
                CampaignMember.campaign_id == campaign_id,
                CampaignMember.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_user_role(
        self,
        session: AsyncSession,
        campaign_id: int,
        telegram_id: int,
    ) -> str | None:
        result = await session.execute(
            select(CampaignMember.role)
            .join(User, User.id == CampaignMember.user_id)
            .where(
                CampaignMember.campaign_id == campaign_id,
                User.telegram_id == telegram_id,
            )
        )

        return result.scalar_one_or_none()

    async def add_or_update_member(
        self,
        session: AsyncSession,
        campaign_id: int,
        user_id: int,
        role: str = "player",
    ) -> CampaignMember:
        member = await self.get_member(
            session=session,
            campaign_id=campaign_id,
            user_id=user_id,
        )

        if member is None:
            return await self.add_member(
                session=session,
                campaign_id=campaign_id,
                user_id=user_id,
                role=role,
            )

        if member.role != "owner":
            member.role = role
            await session.flush()

        return member
