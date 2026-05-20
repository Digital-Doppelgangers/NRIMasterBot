from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from math import ceil
from enum import Enum

class CampaignAction(Enum):
    SELECT = "select"
    DELETE = "delete"

class CampaignCB(CallbackData, prefix="camp"):
    action: str
    campaign_id: int
    page: int

class CharacterAction(Enum):
    VIEW = "view"

class CharacterCB(CallbackData, prefix="char"):
    action: str
    character_id: int
    page: int


class CharacterMenuCB(CallbackData, prefix="chm"):
    action: str
    character_id: int
    page: int


class CharacterEditCB(CallbackData, prefix="che"):
    character_id: int
    scope: str
    field: str
    ability_id: int = 0


class CharacterCampaignCB(CallbackData, prefix="chcamp"):
    character_id: int
    campaign_id: int
    page: int


class NPCAction(Enum):
    VIEW = "view"


class NPCCB(CallbackData, prefix="npc"):
    action: str
    npc_id: int
    page: int


class NPCMenuCB(CallbackData, prefix="npcm"):
    action: str
    npc_id: int
    page: int


class NPCEditCB(CallbackData, prefix="npce"):
    npc_id: int
    field: str


class NPCCampaignCB(CallbackData, prefix="npccamp"):
    npc_id: int
    campaign_id: int
    page: int

PAGE_SIZE = 6

def campaign_list_kb(campaigns: list[dict], action: CampaignAction, page: int = 0) -> InlineKeyboardMarkup:

    total = len(campaigns)
    pages = max(1, ceil(total / PAGE_SIZE))
    page = max(0, min(page, pages - 1))

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    chunk = campaigns[start:end]

    rows: list[list[InlineKeyboardButton]] = []

    # Кнопки кампаний
    for c in chunk:
        rows.append([
            InlineKeyboardButton(
                text=c.title[:40],
                callback_data=CampaignCB(action=action.value, page=page, campaign_id=c.id).pack()
            )
        ])

    # Навигация
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=CampaignCB(action=action.value, page=page - 1, campaign_id=0).pack()))
    nav.append(InlineKeyboardButton(text=f"{page + 1}/{pages}", callback_data="noop"))
    if page < pages - 1:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=CampaignCB(action=action.value, page=page + 1, campaign_id=0).pack()))
    rows.append(nav)

    # Доп. кнопки
    rows.append([InlineKeyboardButton(text="✖️ Закрыть", callback_data="close")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def character_list_kb(characters: list[dict], action: CharacterAction, page: int = 0) -> InlineKeyboardMarkup:

    total = len(characters)
    pages = max(1, ceil(total / PAGE_SIZE))
    page = max(0, min(page, pages - 1))

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    chunk = characters[start:end]

    rows: list[list[InlineKeyboardButton]] = []

    for character in chunk:
        class_name = getattr(character, "class_", None) or "класс неизвестен"
        level = getattr(character, "level", 1) or 1
        text = f"{character.name[:28]} | ур. {level} | {class_name[:18]}"
        rows.append([
            InlineKeyboardButton(
                text=text,
                callback_data=CharacterCB(
                    action=action.value,
                    page=page,
                    character_id=character.id,
                ).pack()
            )
        ])

    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(
            text="⬅️",
            callback_data=CharacterCB(action=action.value, page=page - 1, character_id=0).pack(),
        ))
    nav.append(InlineKeyboardButton(text=f"{page + 1}/{pages}", callback_data="noop"))
    if page < pages - 1:
        nav.append(InlineKeyboardButton(
            text="➡️",
            callback_data=CharacterCB(action=action.value, page=page + 1, character_id=0).pack(),
        ))
    rows.append(nav)

    rows.append([InlineKeyboardButton(text="✖️ Закрыть", callback_data="close")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def character_menu_kb(character_id: int, page: int = 0) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=CharacterMenuCB(action="back", character_id=character_id, page=page).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Изменить персонажа",
                    callback_data=CharacterMenuCB(action="edit", character_id=character_id, page=page).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔗 Присоединить к кампании",
                    callback_data=CharacterMenuCB(action="attach", character_id=character_id, page=page).pack(),
                )
            ],
        ]
    )


def npc_list_kb(npcs: list[dict], action: NPCAction, page: int = 0) -> InlineKeyboardMarkup:
    total = len(npcs)
    pages = max(1, ceil(total / PAGE_SIZE))
    page = max(0, min(page, pages - 1))

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    rows: list[list[InlineKeyboardButton]] = []

    for npc in npcs[start:end]:
        name = getattr(npc, "name", None) or "Без имени"
        role = getattr(npc, "role", None) or "роль не указана"
        text = f"{name[:28]} | {role[:24]}"
        rows.append([
            InlineKeyboardButton(
                text=text,
                callback_data=NPCCB(
                    action=action.value,
                    page=page,
                    npc_id=npc.id,
                ).pack(),
            )
        ])

    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(
            text="⬅️",
            callback_data=NPCCB(action=action.value, page=page - 1, npc_id=0).pack(),
        ))
    nav.append(InlineKeyboardButton(text=f"{page + 1}/{pages}", callback_data="noop"))
    if page < pages - 1:
        nav.append(InlineKeyboardButton(
            text="➡️",
            callback_data=NPCCB(action=action.value, page=page + 1, npc_id=0).pack(),
        ))
    rows.append(nav)
    rows.append([InlineKeyboardButton(text="✖️ Закрыть", callback_data="close")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def npc_menu_kb(npc_id: int, page: int = 0) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=NPCMenuCB(action="back", npc_id=npc_id, page=page).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Изменить NPC",
                    callback_data=NPCMenuCB(action="edit", npc_id=npc_id, page=page).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔗 Добавить к кампании",
                    callback_data=NPCMenuCB(action="attach", npc_id=npc_id, page=page).pack(),
                )
            ],
        ]
    )


def npc_edit_fields_kb(npc_id: int) -> InlineKeyboardMarkup:
    fields = [
        ("Имя", "name"),
        ("Роль", "role"),
        ("Описание", "description"),
        ("Макс. HP", "max_hp"),
        ("Текущее HP", "current_hp"),
        ("Класс брони", "armor_class"),
    ]
    rows = [
        [
            InlineKeyboardButton(
                text=title,
                callback_data=NPCEditCB(npc_id=npc_id, field=field).pack(),
            )
        ]
        for title, field in fields
    ]
    rows.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=NPCMenuCB(action="view", npc_id=npc_id, page=0).pack(),
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def npc_campaigns_kb(npc_id: int, campaigns: list[dict], page: int = 0) -> InlineKeyboardMarkup:
    total = len(campaigns)
    pages = max(1, ceil(total / PAGE_SIZE))
    page = max(0, min(page, pages - 1))

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    rows = [
        [
            InlineKeyboardButton(
                text=campaign.title[:40],
                callback_data=NPCCampaignCB(
                    npc_id=npc_id,
                    campaign_id=campaign.id,
                    page=page,
                ).pack(),
            )
        ]
        for campaign in campaigns[start:end]
    ]

    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(
            text="⬅️",
            callback_data=NPCCampaignCB(npc_id=npc_id, campaign_id=0, page=page - 1).pack(),
        ))
    nav.append(InlineKeyboardButton(text=f"{page + 1}/{pages}", callback_data="noop"))
    if page < pages - 1:
        nav.append(InlineKeyboardButton(
            text="➡️",
            callback_data=NPCCampaignCB(npc_id=npc_id, campaign_id=0, page=page + 1).pack(),
        ))
    rows.append(nav)
    rows.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=NPCMenuCB(action="view", npc_id=npc_id, page=0).pack(),
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def character_edit_sections_kb(character_id: int, page: int = 0) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Основное",
                    callback_data=CharacterEditCB(character_id=character_id, scope="sec", field="identity").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="Класс и происхождение",
                    callback_data=CharacterEditCB(character_id=character_id, scope="sec", field="build").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="Боевые параметры",
                    callback_data=CharacterEditCB(character_id=character_id, scope="sec", field="stats").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="Характеристики",
                    callback_data=CharacterEditCB(character_id=character_id, scope="sec", field="attrs").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="Способности",
                    callback_data=CharacterEditCB(character_id=character_id, scope="sec", field="abilities").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="История",
                    callback_data=CharacterEditCB(character_id=character_id, scope="ch", field="bs").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=CharacterMenuCB(action="view", character_id=character_id, page=page).pack(),
                )
            ],
        ]
    )


def character_edit_fields_kb(character_id: int, section: str) -> InlineKeyboardMarkup:
    sections = {
        "identity": [("Имя", "n"), ("Пол", "g"), ("Возраст", "age")],
        "build": [
            ("Раса", "race"),
            ("Класс", "cl"),
            ("Подкласс", "sub"),
            ("Предыстория", "bg"),
            ("Мировоззрение", "al"),
            ("Уровень", "lvl"),
        ],
        "stats": [("Базовое HP", "hpb"), ("Макс. HP", "mhp"), ("Текущее HP", "chp"), ("Базовый AC", "acb"), ("Класс брони", "ac")],
        "attrs": [("Сила", "str"), ("Ловкость", "dex"), ("Телосложение", "con"), ("Интеллект", "int"), ("Мудрость", "wis"), ("Харизма", "cha")],
    }

    rows = [
        [
            InlineKeyboardButton(
                text=title,
                callback_data=CharacterEditCB(character_id=character_id, scope="ch", field=field).pack(),
            )
        ]
        for title, field in sections.get(section, [])
    ]
    rows.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=CharacterMenuCB(action="edit", character_id=character_id, page=0).pack(),
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def character_abilities_kb(character_id: int, abilities: list[dict]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=ability.name[:40],
                callback_data=CharacterEditCB(
                    character_id=character_id,
                    scope="asel",
                    field="open",
                    ability_id=ability.id,
                ).pack(),
            )
        ]
        for ability in abilities
    ]
    rows.append([
        InlineKeyboardButton(
            text="➕ Добавить способность",
            callback_data=CharacterEditCB(character_id=character_id, scope="addab", field="start").pack(),
        )
    ])
    rows.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=CharacterMenuCB(action="edit", character_id=character_id, page=0).pack(),
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def ability_edit_fields_kb(character_id: int, ability_id: int) -> InlineKeyboardMarkup:
    fields = [
        ("Название", "an"),
        ("Лимит", "ul"),
        ("Форма дистанции", "rs"),
        ("Дистанция, м", "rd"),
        ("Бонусная характеристика", "ba"),
        ("Описание", "ad"),
    ]
    rows = [
        [
            InlineKeyboardButton(
                text=title,
                callback_data=CharacterEditCB(
                    character_id=character_id,
                    scope="ab",
                    field=field,
                    ability_id=ability_id,
                ).pack(),
            )
        ]
        for title, field in fields
    ]
    rows.append([
        InlineKeyboardButton(
            text="🗑 Удалить способность",
            callback_data=CharacterEditCB(
                character_id=character_id,
                scope="delab",
                field="ask",
                ability_id=ability_id,
            ).pack(),
        )
    ])
    rows.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=CharacterEditCB(character_id=character_id, scope="sec", field="abilities").pack(),
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def delete_ability_confirm_kb(character_id: int, ability_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Да, удалить",
                    callback_data=CharacterEditCB(
                        character_id=character_id,
                        scope="delab",
                        field="yes",
                        ability_id=ability_id,
                    ).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="Отмена",
                    callback_data=CharacterEditCB(
                        character_id=character_id,
                        scope="asel",
                        field="open",
                        ability_id=ability_id,
                    ).pack(),
                )
            ],
        ]
    )


def character_campaigns_kb(character_id: int, campaigns: list[dict], page: int = 0) -> InlineKeyboardMarkup:
    total = len(campaigns)
    pages = max(1, ceil(total / PAGE_SIZE))
    page = max(0, min(page, pages - 1))

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    rows = [
        [
            InlineKeyboardButton(
                text=campaign.title[:40],
                callback_data=CharacterCampaignCB(
                    character_id=character_id,
                    campaign_id=campaign.id,
                    page=page,
                ).pack(),
            )
        ]
        for campaign in campaigns[start:end]
    ]

    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(
            text="⬅️",
            callback_data=CharacterCampaignCB(character_id=character_id, campaign_id=0, page=page - 1).pack(),
        ))
    nav.append(InlineKeyboardButton(text=f"{page + 1}/{pages}", callback_data="noop"))
    if page < pages - 1:
        nav.append(InlineKeyboardButton(
            text="➡️",
            callback_data=CharacterCampaignCB(character_id=character_id, campaign_id=0, page=page + 1).pack(),
        ))
    rows.append(nav)
    rows.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=CharacterMenuCB(action="view", character_id=character_id, page=0).pack(),
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)
