from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User


class UserRepository:
    async def get_by_telegram_id(
        self,
        session: AsyncSession,
        telegram_id: int,
    ) -> User | None:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )

        return result.scalar_one_or_none()

    async def create_user(
        self,
        session: AsyncSession,
        telegram_id: int,
        username: str | None,
        display_name: str | None,
    ) -> User:
        user = User(
            telegram_id=telegram_id,
            username=username,
            display_name=display_name,
        )

        session.add(user)
        await session.flush()

        return user

    async def get_or_create_user(
        self,
        session: AsyncSession,
        telegram_id: int,
        username: str | None,
        display_name: str | None,
    ) -> User:
        user = await self.get_by_telegram_id(session, telegram_id)

        if user:
            return user

        return await self.create_user(
            session=session,
            telegram_id=telegram_id,
            username=username,
            display_name=display_name,
        )
    
    async def set_active_campaign_to_user(
    self,
    session: AsyncSession,
    telegram_id: int,
    active_campaign_id: int,
) -> bool:
        result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )

        user = result.scalar_one_or_none()

        if user is None:
            return False

        user.active_campaign_id = active_campaign_id

        await session.commit()

        return True
