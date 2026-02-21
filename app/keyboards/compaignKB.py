from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from math import ceil

class CampaignListCB(CallbackData, prefix="camp_list"):
    page: int

class CampaignSelectCB(CallbackData, prefix="camp_sel"):
    campaign_id: int

def campaign_list_kb(campaigns: list[dict], page: int = 0, page_size: int = 6) -> InlineKeyboardMarkup:

    total = len(campaigns)
    pages = max(1, ceil(total / page_size))
    page = max(0, min(page, pages - 1))

    start = page * page_size
    end = start + page_size
    chunk = campaigns[start:end]

    rows: list[list[InlineKeyboardButton]] = []

    # Кнопки кампаний
    for c in chunk:
        rows.append([
            InlineKeyboardButton(
                text=c.title[:40],
                callback_data=CampaignSelectCB(campaign_id=c.id).pack()
            )
        ])

    # Навигация
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=CampaignListCB(page=page - 1).pack()))
    nav.append(InlineKeyboardButton(text=f"{page + 1}/{pages}", callback_data="noop"))
    if page < pages - 1:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=CampaignListCB(page=page + 1).pack()))
    rows.append(nav)

    # Доп. кнопки
    rows.append([InlineKeyboardButton(text="✖️ Закрыть", callback_data="close")])

    return InlineKeyboardMarkup(inline_keyboard=rows)