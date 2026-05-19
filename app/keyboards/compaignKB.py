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
