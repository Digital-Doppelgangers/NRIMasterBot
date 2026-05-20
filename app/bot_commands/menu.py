from aiogram import Bot
from aiogram.types import BotCommand


BOT_COMMANDS = [
    BotCommand(command="start", description="Запустить бота"),
    BotCommand(command="help", description="Справка по командам"),
    BotCommand(command="campaign_new", description="Создать кампанию"),
    BotCommand(command="campaign_list", description="Список кампаний"),
    BotCommand(command="campaign_current", description="Текущая кампания"),
    BotCommand(command="campaign_delete", description="Удалить кампанию"),
    BotCommand(command="create_character", description="Создать персонажа"),
    BotCommand(command="my_characters", description="Мои персонажи"),
    BotCommand(command="create_npc", description="Создать NPC"),
    BotCommand(command="my_npcs", description="Мои NPC"),
]


async def setup_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(BOT_COMMANDS)
