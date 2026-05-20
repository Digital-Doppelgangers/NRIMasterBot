from datetime import datetime

from decimal import Decimal

from sqlalchemy import BigInteger, String, Text, Boolean, DateTime, ForeignKey, Enum, Integer, Numeric
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func



class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="free")
    active_campaign_id: Mapped[int | None] = mapped_column( BigInteger, ForeignKey("campaigns.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True,)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    system_title: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class CampaignMember(Base):
    __tablename__ = "campaign_members"

    campaign_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("campaigns.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )

    role: Mapped[str] = mapped_column(
        Enum("owner", "gm", "player", "viewer"),
        nullable=False,
        default="player",
    )


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    owner_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    gender: Mapped[str | None] = mapped_column(Enum("male", "female", "other"), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    race: Mapped[str | None] = mapped_column(String(64), nullable=True)
    class_: Mapped[str | None] = mapped_column("class", String(64), nullable=True)
    subclass: Mapped[str | None] = mapped_column(String(64), nullable=True)
    background: Mapped[str | None] = mapped_column(String(128), nullable=True)
    alignment: Mapped[str | None] = mapped_column(String(64), nullable=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    hp_base: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_hp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_hp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ac_base: Mapped[int | None] = mapped_column(Integer, nullable=True)
    armor_class: Mapped[int | None] = mapped_column(Integer, nullable=True)
    str_mod: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dex_mod: Mapped[int | None] = mapped_column(Integer, nullable=True)
    con_mod: Mapped[int | None] = mapped_column(Integer, nullable=True)
    int_mod: Mapped[int | None] = mapped_column(Integer, nullable=True)
    wis_mod: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cha_mod: Mapped[int | None] = mapped_column(Integer, nullable=True)
    backstory: Mapped[str | None] = mapped_column(Text, nullable=True)
    lifecycle_status: Mapped[str] = mapped_column(
        Enum("available", "in_campaign", "archived"),
        nullable=False,
        default="available",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class CampaignCharacter(Base):
    __tablename__ = "campaign_characters"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("campaigns.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    character_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("characters.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class NPC(Base):
    __tablename__ = "npcs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    owner_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    campaign_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("campaigns.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    max_hp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_hp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    armor_class: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Ability(Base):
    __tablename__ = "abilities"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    character_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("characters.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    ability_kind: Mapped[str] = mapped_column(
        Enum("attack", "control", "strong_attack", "support"),
        nullable=False,
    )
    usage_limit: Mapped[str] = mapped_column(
        Enum("at_will", "1/combat", "2/short_rest", "1/rest"),
        nullable=False,
    )
    range_shape: Mapped[str] = mapped_column(
        Enum("touch", "melee", "ranged", "cone", "line", "sphere"),
        nullable=False,
    )
    range_distance_m: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    bonus_ability: Mapped[str] = mapped_column(
        Enum("str", "dex", "con", "int", "wis", "cha"),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)


class AbilityDamage(Base):
    __tablename__ = "ability_damage"

    ability_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("abilities.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    dice: Mapped[str] = mapped_column(String(16), nullable=False)
    damage_type: Mapped[str] = mapped_column(
        Enum(
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
        ),
        nullable=False,
    )


class AbilityControl(Base):
    __tablename__ = "ability_control"

    ability_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("abilities.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    control_type: Mapped[str] = mapped_column(
        Enum("charm", "blind", "stun", "fear", "slow", "silence", "push", "prone"),
        nullable=False,
    )
    duration_rounds: Mapped[int] = mapped_column(Integer, nullable=False)
    condition_end: Mapped[str] = mapped_column(String(255), nullable=False)


class AbilitySupport(Base):
    __tablename__ = "ability_support"

    ability_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("abilities.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    support_type: Mapped[str] = mapped_column(
        Enum("heal", "buff_roll", "buff_damage", "buff_to_hit", "extra_action", "cleanse"),
        nullable=False,
    )
    check_dc: Mapped[int | None] = mapped_column(Integer, nullable=True)
    check_attr: Mapped[str | None] = mapped_column(Enum("str", "dex", "con", "int", "wis", "cha"), nullable=True)
    dice: Mapped[str | None] = mapped_column(String(16), nullable=True)
    action_type: Mapped[str | None] = mapped_column(Enum("bonus_action", "reaction", "move"), nullable=True)
    cleanse_target: Mapped[str | None] = mapped_column(
        Enum("blind", "fear", "charm", "stun", "slow", "silence", "prone"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
