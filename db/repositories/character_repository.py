from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import (
    Ability,
    AbilityControl,
    AbilityDamage,
    AbilitySupport,
    Campaign,
    CampaignCharacter,
    CampaignMember,
    Character,
    User,
)
from db.repositories.user_repository import UserRepository


VALID_ABILITY_KINDS = {"attack", "control", "strong_attack", "support"}
VALID_USAGE_LIMITS = {"at_will", "1/combat", "2/short_rest", "1/rest"}
VALID_RANGE_SHAPES = {"touch", "melee", "ranged", "cone", "line", "sphere"}
VALID_ATTRIBUTES = {"str", "dex", "con", "int", "wis", "cha"}
VALID_DAMAGE_TYPES = {
    "slashing",
    "piercing",
    "bludgeoning",
    "fire",
    "cold",
    "lightning",
    "poison",
    "acid",
    "psychic",
    "necrotic",
    "radiant",
    "thunder",
}
VALID_CONTROL_TYPES = {"charm", "blind", "stun", "fear", "slow", "silence", "push", "prone"}
VALID_CLEANSE_TARGETS = {"blind", "fear", "charm", "stun", "slow", "silence", "prone"}
VALID_SUPPORT_TYPES = {"heal", "buff_roll", "buff_damage", "buff_to_hit", "extra_action", "cleanse"}
VALID_ACTION_TYPES = {"bonus_action", "reaction", "move"}


def _clean_text(value: Any, default: str | None = None, max_len: int | None = None) -> str | None:
    if value is None:
        return default

    text = str(value).strip()
    if not text:
        return default

    if max_len is not None:
        return text[:max_len]

    return text


def _clean_int(value: Any, default: int | None = None) -> int | None:
    if value is None:
        return default

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _clean_decimal(value: Any, default: Decimal = Decimal("1.00")) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default


def _choice(value: Any, allowed: set[str], default: str) -> str:
    text = _clean_text(value)
    if text in allowed:
        return text
    return default


class CharacterRepository:
    def __init__(self) -> None:
        self.user_repository = UserRepository()

    async def create_from_generated_data(
        self,
        session: AsyncSession,
        telegram_id: int,
        username: str | None,
        display_name: str | None,
        data: dict[str, Any],
    ) -> Character:
        user = await self.user_repository.get_or_create_user(
            session=session,
            telegram_id=telegram_id,
            username=username,
            display_name=display_name,
        )

        identity = data.get("identity") or {}
        build = data.get("build") or {}
        base_stats = data.get("base_stats") or {}
        attrs = data.get("attributes_mods") or {}
        backstory = data.get("backstory") or {}

        hp_base = _clean_int(base_stats.get("hp_base"))
        ac_base = _clean_int(base_stats.get("ac_base"))
        active_campaign_id = user.active_campaign_id

        character = Character(
            owner_user_id=user.id,
            name=_clean_text(identity.get("name"), "Без имени", 128),
            gender=_choice(identity.get("gender"), {"male", "female", "other"}, "other"),
            age=_clean_int(identity.get("age")),
            race=_clean_text(build.get("race"), max_len=64),
            class_=_clean_text(build.get("class"), max_len=64),
            subclass=_clean_text(build.get("subclass"), max_len=64),
            background=_clean_text(build.get("background"), max_len=128),
            alignment=_clean_text(build.get("alignment"), max_len=64),
            level=_clean_int(build.get("level"), 1) or 1,
            hp_base=hp_base,
            max_hp=hp_base,
            current_hp=hp_base,
            ac_base=ac_base,
            armor_class=ac_base,
            str_mod=_clean_int(attrs.get("str")),
            dex_mod=_clean_int(attrs.get("dex")),
            con_mod=_clean_int(attrs.get("con")),
            int_mod=_clean_int(attrs.get("int")),
            wis_mod=_clean_int(attrs.get("wis")),
            cha_mod=_clean_int(attrs.get("cha")),
            backstory=_clean_text(backstory.get("story")),
            lifecycle_status="in_campaign" if active_campaign_id else "available",
        )

        session.add(character)
        await session.flush()

        if active_campaign_id:
            session.add(
                CampaignCharacter(
                    campaign_id=active_campaign_id,
                    character_id=character.id,
                    is_active=True,
                )
            )

        for ability_data in data.get("abilities") or []:
            await self._add_ability(session, character.id, ability_data)

        await session.commit()
        await session.refresh(character)

        return character

    async def list_user_characters(
        self,
        session: AsyncSession,
        telegram_id: int,
    ) -> list[Character]:
        return await self.list_by_user(session=session, telegram_id=telegram_id)

    async def list_by_user(
        self,
        session: AsyncSession,
        telegram_id: int,
    ) -> list[Character]:
        result = await session.execute(
            select(Character)
            .join(User, User.id == Character.owner_user_id)
            .where(User.telegram_id == telegram_id)
            .order_by(Character.created_at.desc())
        )

        return list(result.scalars().all())

    async def get_user_character(
        self,
        session: AsyncSession,
        telegram_id: int,
        character_id: int,
    ) -> Character | None:
        result = await session.execute(
            select(Character)
            .join(User, User.id == Character.owner_user_id)
            .where(User.telegram_id == telegram_id, Character.id == character_id)
        )

        return result.scalar_one_or_none()

    async def get_user_character_data(
        self,
        session: AsyncSession,
        telegram_id: int,
        character_id: int,
    ) -> dict[str, Any] | None:
        character = await self.get_user_character(
            session=session,
            telegram_id=telegram_id,
            character_id=character_id,
        )

        if character is None:
            return None

        return await self.to_generated_data(session, character)

    async def to_generated_data(
        self,
        session: AsyncSession,
        character: Character,
    ) -> dict[str, Any]:
        result = await session.execute(
            select(Ability)
            .where(Ability.character_id == character.id)
            .order_by(Ability.id.asc())
        )
        abilities = [
            await self._ability_to_generated_data(session, ability)
            for ability in result.scalars().all()
        ]

        return {
            "meta": {"system": "lite_d20", "version": "mvp_v1"},
            "identity": {
                "name": character.name,
                "gender": character.gender,
                "age": character.age,
            },
            "build": {
                "race": character.race,
                "class": character.class_,
                "subclass": character.subclass,
                "background": character.background,
                "level": character.level,
                "alignment": character.alignment,
            },
            "base_stats": {
                "hp_base": character.hp_base,
                "ac_base": character.ac_base,
            },
            "attributes_mods": {
                "str": character.str_mod,
                "dex": character.dex_mod,
                "con": character.con_mod,
                "int": character.int_mod,
                "wis": character.wis_mod,
                "cha": character.cha_mod,
            },
            "abilities": abilities,
            "backstory": {"story": character.backstory},
        }

    async def list_character_abilities(
        self,
        session: AsyncSession,
        telegram_id: int,
        character_id: int,
    ) -> list[Ability]:
        character = await self.get_user_character(
            session=session,
            telegram_id=telegram_id,
            character_id=character_id,
        )
        if character is None:
            return []

        result = await session.execute(
            select(Ability)
            .where(Ability.character_id == character_id)
            .order_by(Ability.id.asc())
        )

        return list(result.scalars().all())

    async def update_character_field(
        self,
        session: AsyncSession,
        telegram_id: int,
        character_id: int,
        field: str,
        value: str,
    ) -> Character | None:
        character = await self.get_user_character(
            session=session,
            telegram_id=telegram_id,
            character_id=character_id,
        )
        if character is None:
            return None

        text_fields = {
            "name": 128,
            "race": 64,
            "class_": 64,
            "subclass": 64,
            "background": 128,
            "alignment": 64,
            "backstory": None,
        }
        int_fields = {
            "age",
            "level",
            "hp_base",
            "max_hp",
            "current_hp",
            "ac_base",
            "armor_class",
            "str_mod",
            "dex_mod",
            "con_mod",
            "int_mod",
            "wis_mod",
            "cha_mod",
        }

        if field == "gender":
            character.gender = _choice(value, {"male", "female", "other"}, "other")
        elif field in text_fields:
            setattr(character, field, _clean_text(value, max_len=text_fields[field]))
        elif field in int_fields:
            setattr(character, field, _clean_int(value))
        else:
            return None

        await session.commit()
        await session.refresh(character)
        return character

    async def update_ability_field(
        self,
        session: AsyncSession,
        telegram_id: int,
        character_id: int,
        ability_id: int,
        field: str,
        value: str,
    ) -> Ability | None:
        character = await self.get_user_character(
            session=session,
            telegram_id=telegram_id,
            character_id=character_id,
        )
        if character is None:
            return None

        result = await session.execute(
            select(Ability).where(
                Ability.id == ability_id,
                Ability.character_id == character_id,
            )
        )
        ability = result.scalar_one_or_none()
        if ability is None:
            return None

        if field == "name":
            ability.name = _clean_text(value, "Без названия", 128) or "Без названия"
        elif field == "usage_limit":
            ability.usage_limit = _choice(value, VALID_USAGE_LIMITS, ability.usage_limit)
        elif field == "range_shape":
            ability.range_shape = _choice(value, VALID_RANGE_SHAPES, ability.range_shape)
        elif field == "range_distance_m":
            ability.range_distance_m = _clean_decimal(value, ability.range_distance_m)
        elif field == "bonus_ability":
            ability.bonus_ability = _choice(value, VALID_ATTRIBUTES, ability.bonus_ability)
        elif field == "description":
            ability.description = _clean_text(value, max_len=500)
        else:
            return None

        await session.commit()
        await session.refresh(ability)
        return ability

    async def create_ability_for_user(
        self,
        session: AsyncSession,
        telegram_id: int,
        character_id: int,
        ability_data: dict[str, Any],
    ) -> Ability | None:
        character = await self.get_user_character(
            session=session,
            telegram_id=telegram_id,
            character_id=character_id,
        )
        if character is None:
            return None

        ability = await self._add_ability(session, character_id, ability_data)
        await session.commit()
        await session.refresh(ability)
        return ability

    async def delete_ability_for_user(
        self,
        session: AsyncSession,
        telegram_id: int,
        character_id: int,
        ability_id: int,
    ) -> bool:
        character = await self.get_user_character(
            session=session,
            telegram_id=telegram_id,
            character_id=character_id,
        )
        if character is None:
            return False

        result = await session.execute(
            select(Ability).where(
                Ability.id == ability_id,
                Ability.character_id == character_id,
            )
        )
        ability = result.scalar_one_or_none()
        if ability is None:
            return False

        await session.delete(ability)
        await session.commit()
        return True

    async def attach_to_campaign(
        self,
        session: AsyncSession,
        telegram_id: int,
        character_id: int,
        campaign_id: int,
    ) -> bool:
        character = await self.get_user_character(
            session=session,
            telegram_id=telegram_id,
            character_id=character_id,
        )
        if character is None:
            return False

        campaign_result = await session.execute(
            select(Campaign)
            .join(CampaignMember, Campaign.id == CampaignMember.campaign_id)
            .join(User, User.id == CampaignMember.user_id)
            .where(Campaign.id == campaign_id, User.telegram_id == telegram_id)
        )
        campaign = campaign_result.scalar_one_or_none()
        if campaign is None:
            return False

        existing_result = await session.execute(
            select(CampaignCharacter).where(
                CampaignCharacter.campaign_id == campaign_id,
                CampaignCharacter.character_id == character_id,
            )
        )
        existing = existing_result.scalar_one_or_none()

        if existing:
            existing.is_active = True
        else:
            session.add(
                CampaignCharacter(
                    campaign_id=campaign_id,
                    character_id=character_id,
                    is_active=True,
                )
            )

        character.lifecycle_status = "in_campaign"
        await session.commit()
        return True

    async def _add_ability(
        self,
        session: AsyncSession,
        character_id: int,
        ability_data: dict[str, Any],
    ) -> Ability:
        range_data = ability_data.get("range") or {}
        ability_kind = _choice(ability_data.get("type"), VALID_ABILITY_KINDS, "attack")
        ability = Ability(
            character_id=character_id,
            name=_clean_text(ability_data.get("name"), "Без названия", 128),
            ability_kind=ability_kind,
            usage_limit=_choice(ability_data.get("limit"), VALID_USAGE_LIMITS, "at_will"),
            range_shape=_choice(range_data.get("shape"), VALID_RANGE_SHAPES, "melee"),
            range_distance_m=_clean_decimal(range_data.get("distance_m")),
            bonus_ability=_choice(ability_data.get("bonus_ability"), VALID_ATTRIBUTES, "str"),
            description=_clean_text(ability_data.get("description"), max_len=500),
        )

        session.add(ability)
        await session.flush()

        damage = ability_data.get("damage")
        if damage or ability_kind in {"attack", "strong_attack"}:
            damage = damage or {}
            session.add(
                AbilityDamage(
                    ability_id=ability.id,
                    dice=_clean_text(damage.get("dice"), "1d4", 16),
                    damage_type=_choice(damage.get("type"), VALID_DAMAGE_TYPES, "bludgeoning"),
                )
            )

        control = ability_data.get("control")
        if control or ability_kind == "control":
            control = control or {}
            session.add(
                AbilityControl(
                    ability_id=ability.id,
                    control_type=_choice(control.get("type"), VALID_CONTROL_TYPES, "prone"),
                    duration_rounds=_clean_int(control.get("duration_rounds"), 1) or 1,
                    condition_end=_clean_text(control.get("condition_end"), "До конца сцены", 255),
                )
            )

        support = ability_data.get("support")
        if support or ability_kind == "support":
            support = support or {}
            session.add(self._build_support_row(ability.id, support))

        return ability

    def _build_support_row(
        self,
        ability_id: int,
        support: dict[str, Any],
    ) -> AbilitySupport:
        check = support.get("check") or {}
        value = support.get("value") or {}
        removes = value.get("removes") or []

        return AbilitySupport(
            ability_id=ability_id,
            support_type=_choice(support.get("type"), VALID_SUPPORT_TYPES, "heal"),
            check_dc=_clean_int(check.get("dc")),
            check_attr=_choice(check.get("dc_plus_attr"), VALID_ATTRIBUTES, "str")
            if check.get("dc_plus_attr")
            else None,
            dice=_clean_text(value.get("dice"), max_len=16),
            action_type=_choice(value.get("action"), VALID_ACTION_TYPES, "bonus_action")
            if value.get("action")
            else None,
            cleanse_target=_choice(removes[0], VALID_CLEANSE_TARGETS, "blind") if removes else None,
            notes=_clean_text(support.get("notes"), max_len=255),
        )

    async def _ability_to_generated_data(
        self,
        session: AsyncSession,
        ability: Ability,
    ) -> dict[str, Any]:
        data: dict[str, Any] = {
            "name": ability.name,
            "type": ability.ability_kind,
            "limit": ability.usage_limit,
            "range": {
                "shape": ability.range_shape,
                "distance_m": float(ability.range_distance_m),
            },
            "bonus_ability": ability.bonus_ability,
            "damage": None,
            "control": None,
            "support": None,
            "description": ability.description,
        }

        damage_result = await session.execute(
            select(AbilityDamage).where(AbilityDamage.ability_id == ability.id)
        )
        damage = damage_result.scalar_one_or_none()
        if damage:
            data["damage"] = {
                "dice": damage.dice,
                "type": damage.damage_type,
            }

        control_result = await session.execute(
            select(AbilityControl).where(AbilityControl.ability_id == ability.id)
        )
        control = control_result.scalar_one_or_none()
        if control:
            data["control"] = {
                "type": control.control_type,
                "duration_rounds": control.duration_rounds,
                "condition_end": control.condition_end,
            }

        support_result = await session.execute(
            select(AbilitySupport).where(AbilitySupport.ability_id == ability.id)
        )
        support = support_result.scalar_one_or_none()
        if support:
            data["support"] = {
                "type": support.support_type,
                "check": {
                    "dc": support.check_dc,
                    "dc_plus_attr": support.check_attr,
                }
                if support.check_dc or support.check_attr
                else None,
                "value": self._support_value_to_generated_data(support),
                "notes": support.notes,
            }

        return data

    def _support_value_to_generated_data(self, support: AbilitySupport) -> dict[str, Any] | None:
        if support.dice:
            return {"dice": support.dice}

        if support.action_type:
            return {"action": support.action_type}

        if support.cleanse_target:
            return {"removes": [support.cleanse_target]}

        return None
