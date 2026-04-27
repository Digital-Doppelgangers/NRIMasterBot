from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Campaign, CampaignMember, User
from db.repositories.user_repository import UserRepository
from db.repositories.campaign_member_repository import CampaignMemberRepository


class CampaignRepository:
    def __init__(self):
        self.user_repository = UserRepository()
        self.campaign_member_repository = CampaignMemberRepository()

    async def create_campaign(
        self,
        session: AsyncSession,
        telegram_id: int,
        username: str | None,
        display_name: str | None,
        title: str,
        description: str | None = None,
        system_title: str = "lite_d20",
        is_public: bool = False,
    ) -> Campaign:
        user = await self.user_repository.get_or_create_user(
            session=session,
            telegram_id=telegram_id,
            username=username,
            display_name=display_name,
        )

        campaign = Campaign(
            title=title,
            description=description,
            system_title=system_title,
            is_public=is_public,
        )

        session.add(campaign)
        await session.flush()

        await self.campaign_member_repository.add_member(
            session=session,
            campaign_id=campaign.id,
            user_id=user.id,
            role="owner",
        )

        await session.commit()
        await session.refresh(campaign)

        return campaign

    async def get_by_id(
        self,
        session: AsyncSession,
        campaign_id: int,
    ) -> Campaign | None:
        result = await session.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )

        return result.scalar_one_or_none()

    async def get_user_campaigns(
        self,
        session: AsyncSession,
        telegram_id: int,
    ) -> list[Campaign]:
        result = await session.execute(
            select(Campaign)
            .join(CampaignMember, Campaign.id == CampaignMember.campaign_id)
            .join(User, User.id == CampaignMember.user_id)
            .where(User.telegram_id == telegram_id)
            .order_by(Campaign.created_at.desc())
        )

        return list(result.scalars().all())

    async def is_user_campaign_owner(
        self,
        session: AsyncSession,
        telegram_id: int,
        campaign_id: int,
    ) -> bool:
        result = await session.execute(
            select(CampaignMember)
            .join(User, User.id == CampaignMember.user_id)
            .where(
                CampaignMember.campaign_id == campaign_id,
                User.telegram_id == telegram_id,
                CampaignMember.role == "owner",
            )
        )

        return result.scalar_one_or_none() is not None

    async def update_campaign(
        self,
        session: AsyncSession,
        telegram_id: int,
        campaign_id: int,
        title: str | None = None,
        description: str | None = None,
        is_public: bool | None = None,
    ) -> Campaign | None:
        is_owner = await self.is_user_campaign_owner(
            session=session,
            telegram_id=telegram_id,
            campaign_id=campaign_id,
        )

        if not is_owner:
            return None

        campaign = await self.get_by_id(
            session=session,
            campaign_id=campaign_id,
        )

        if campaign is None:
            return None

        if title is not None:
            campaign.title = title

        if description is not None:
            campaign.description = description

        if is_public is not None:
            campaign.is_public = is_public

        await session.commit()
        await session.refresh(campaign)

        return campaign

    async def delete_campaign_by_owner(
        self,
        session: AsyncSession,
        telegram_id: int,
        campaign_id: int,
    ) -> bool:
        is_owner = await self.is_user_campaign_owner(
            session=session,
            telegram_id=telegram_id,
            campaign_id=campaign_id,
        )

        if not is_owner:
            return False

        campaign = await self.get_by_id(
            session=session,
            campaign_id=campaign_id,
        )

        if campaign is None:
            return False

        await session.delete(campaign)
        await session.commit()

        return True