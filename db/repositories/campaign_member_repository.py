from sqlalchemy.ext.asyncio import AsyncSession

from db.models import CampaignMember
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