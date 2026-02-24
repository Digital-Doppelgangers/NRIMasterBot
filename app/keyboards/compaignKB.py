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