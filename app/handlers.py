from aiogram import F, Router 
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram import F
from aiogram.types import CallbackQuery
from aiogram.enums import ParseMode
from db.database import async_session

from app.formatters.character_parser import parse_character_response
from app.formatters.character_message_formatter import format_character_message
from app.formatters.npc_message_formatter import format_npc_message
from app.keyboards.compaignKB import*
from app.repos.memory_campaign_repo import*
from app.llm_client import ask_llm
from app.prompts import*
from db.repositories.user_repository import UserRepository
from db.repositories.campaign_repository import CampaignRepository
from db.repositories.character_repository import CharacterRepository
from db.repositories.npc_repository import NPCRepository

router = Router()
campaign_repo = InMemoryCampaignRepo()
campaign_repository = CampaignRepository()
user_repository = UserRepository()
character_repository = CharacterRepository()
npc_repository = NPCRepository()

WAIT_MESSAGE_GIF_URL="https://media1.tenor.com/m/OuPsTzfoh6cAAAAd/%D1%82%D0%B0%D0%BA%D0%B8%D0%B7%D0%B0%D0%BF%D0%B8%D1%88%D0%B5%D0%BC-%D0%B7%D0%B0%D0%BF%D0%B8%D1%88%D0%B5%D0%BC.gif"

COMMAND_ALIASES = {
    "/start",
    "/help",
    "/campaign_new",
    "/campaign_list",
    "/campaign_current",
    "/campaign_delete",
    "/create_character",
    "/my_characters",
    "/create_npc",
    "/my_npcs",
    "/npc_list",
    "/npcs",
    "/characters",
    "start",
    "help",
    "campaign new",
    "campaign_new",
    "create campaign",
    "new campaign",
    "campaign list",
    "campaign_list",
    "campaign current",
    "campaign_current",
    "campaign delete",
    "campaign_delete",
    "create character",
    "create_character",
    "my characters",
    "my_characters",
    "characters",
    "create npc",
    "create_npc",
    "npc new",
    "npc_new",
    "my npcs",
    "my_npcs",
    "npc list",
    "npc_list",
    "npcs",
}


def is_command_like_text(text: str | None) -> bool:
    if not text:
        return False

    normalized = " ".join(text.strip().casefold().split())
    command = normalized.split("@", 1)[0]
    return command.startswith("/") or normalized in COMMAND_ALIASES


async def reject_command_as_input(message: Message, state: FSMContext) -> bool:
    if not is_command_like_text(message.text):
        return False

    await state.clear()
    await message.answer(
        "Это похоже на команду, поэтому я не буду сохранять ее как название или значение.\n"
        "Текущий ввод отменен. Отправь нужную команду еще раз."
    )
    return True

class CreatecharacterStates(StatesGroup):
    userGavePrompt = State()

class EditCharacterStates(StatesGroup):
    waiting_for_value = State()

class AddAbilityStates(StatesGroup):
    waiting_for_value = State()

class CreateNPCStates(StatesGroup):
    waiting_for_value = State()

class EditNPCStates(StatesGroup):
    waiting_for_value = State()

class CreateCampaignStates(StatesGroup):
    userGaveCampaignName = State()
    userGaveCampaignDescription = State()


class InviteCampaignMemberStates(StatesGroup):
    waiting_for_username = State()


CHARACTER_FIELD_LABELS = {
    "name": "имя",
    "gender": "пол",
    "age": "возраст",
    "race": "расу",
    "class_": "класс",
    "subclass": "подкласс",
    "background": "предысторию",
    "alignment": "мировоззрение",
    "level": "уровень",
    "hp_base": "базовое HP",
    "max_hp": "максимальное HP",
    "current_hp": "текущее HP",
    "ac_base": "базовый AC",
    "armor_class": "класс брони",
    "str_mod": "модификатор силы",
    "dex_mod": "модификатор ловкости",
    "con_mod": "модификатор телосложения",
    "int_mod": "модификатор интеллекта",
    "wis_mod": "модификатор мудрости",
    "cha_mod": "модификатор харизмы",
    "backstory": "историю",
}

ABILITY_FIELD_LABELS = {
    "name": "название способности",
    "usage_limit": "лимит использования",
    "range_shape": "форму дистанции",
    "range_distance_m": "дистанцию в метрах",
    "bonus_ability": "бонусную характеристику",
    "description": "описание способности",
}

FIELD_HINTS = {
    "name": "Это обязательное поле в базе. Если отправить '-' или пустоту, сохранится '-'.",
    "gender": "Допустимые значения базы: male, female, other. Если отправить '-' или что-то другое, поле останется пустым.",
    "race": "Можно писать свободно. Например: человек, эльф, кованый, грибной аристократ. '-' оставит поле пустым.",
    "class_": "Можно писать свободно. Например: воин, маг, ведьма, рыцарь пепла. '-' оставит поле пустым.",
    "subclass": "Можно писать свободно или оставить пустым через '-'.",
    "background": "Можно писать свободно. Например: изгнанник, городской лекарь, бывший пират. '-' оставит поле пустым.",
    "alignment": "Можно писать свободно. Например: хаотично-добрый, прагматик, верен клятве. '-' оставит поле пустым.",
    "backstory": "Можно писать в любом формате. '-' оставит поле пустым.",
    "level": "Это обязательное числовое поле в базе. Если ввести не число или '-', сохранится 1.",
    "age": "Числовое поле: если ввести текст или '-', сохранится пустое значение.",
    "hp_base": "Числовое поле: если ввести текст или '-', сохранится пустое значение.",
    "max_hp": "Числовое поле: если ввести текст или '-', сохранится пустое значение.",
    "current_hp": "Числовое поле: если ввести текст или '-', сохранится пустое значение.",
    "ac_base": "Числовое поле: если ввести текст или '-', сохранится пустое значение.",
    "armor_class": "Числовое поле: если ввести текст или '-', сохранится пустое значение.",
    "str_mod": "Числовое поле: если ввести текст или '-', сохранится пустое значение.",
    "dex_mod": "Числовое поле: если ввести текст или '-', сохранится пустое значение.",
    "con_mod": "Числовое поле: если ввести текст или '-', сохранится пустое значение.",
    "int_mod": "Числовое поле: если ввести текст или '-', сохранится пустое значение.",
    "wis_mod": "Числовое поле: если ввести текст или '-', сохранится пустое значение.",
    "cha_mod": "Числовое поле: если ввести текст или '-', сохранится пустое значение.",
    "usage_limit": "Допустимые значения базы: at_will, 1/combat, 2/short_rest, 1/rest. Если ввести другое, старое значение сохранится.",
    "range_shape": "Допустимые значения базы: touch, melee, ranged, cone, line, sphere. Если ввести другое, старое значение сохранится.",
    "bonus_ability": "Допустимые значения базы: str, dex, con, int, wis, cha. Если ввести другое, старое значение сохранится.",
}

NPC_FIELDS = ["name", "role", "description", "max_hp", "current_hp", "armor_class"]

NPC_FIELD_LABELS = {
    "name": "имя",
    "role": "роль",
    "description": "описание",
    "max_hp": "максимальное HP",
    "current_hp": "текущее HP",
    "armor_class": "класс брони",
}

NPC_FIELD_PROMPTS = {
    "name": "Имя NPC. Например: Марта из гавани. Можно отправить '-' и оставить пустым.",
    "role": "Роль NPC. Например: трактирщица, тайный информатор, капитан стражи. Можно писать свободно или отправить '-'.",
    "description": "Описание NPC: внешность, характер, секреты, зацепки. Можно отправить '-' и оставить пустым.",
    "max_hp": "Максимальное HP числом. Например: 12. Если не нужно, отправь '-'.",
    "current_hp": "Текущее HP числом. Например: 12. Если не нужно, отправь '-'.",
    "armor_class": "Класс брони числом. Например: 10, 13, 16. Если не нужно, отправь '-'.",
}

NPC_FIELD_HINTS = {
    "role": "Варианты для вдохновения: торговец, союзник, враг, информатор, наставник, слуга, стражник, культист.",
    "description": "Можно указать заметки в любом формате. Бот не будет приводить это поле к списку вариантов.",
    "max_hp": "Это числовое поле: если ввести текст, сохранится пустое значение.",
    "current_hp": "Это числовое поле: если ввести текст, сохранится пустое значение.",
    "armor_class": "Это числовое поле: если ввести текст, сохранится пустое значение.",
}

EDIT_SCOPE_CODES = {
    "sec": "section",
    "ch": "character",
    "asel": "ability_select",
    "ab": "ability",
    "addab": "add_ability",
    "delab": "delete_ability",
}

EDIT_FIELD_CODES = {
    "n": "name",
    "g": "gender",
    "cl": "class_",
    "sub": "subclass",
    "bg": "background",
    "al": "alignment",
    "lvl": "level",
    "hpb": "hp_base",
    "mhp": "max_hp",
    "chp": "current_hp",
    "acb": "ac_base",
    "ac": "armor_class",
    "str": "str_mod",
    "dex": "dex_mod",
    "con": "con_mod",
    "int": "int_mod",
    "wis": "wis_mod",
    "cha": "cha_mod",
    "bs": "backstory",
    "an": "name",
    "ul": "usage_limit",
    "rs": "range_shape",
    "rd": "range_distance_m",
    "ba": "bonus_ability",
    "ad": "description",
}

ABILITY_ADD_STEPS = {
    "common": ["name", "type", "limit", "range_shape", "range_distance_m", "bonus_ability", "description"],
    "damage": ["damage_dice", "damage_type"],
    "control": ["control_type", "duration_rounds", "condition_end"],
    "support": ["support_type", "check_dc", "check_attr", "support_dice", "action_type", "cleanse_target", "notes"],
}

ABILITY_ADD_PROMPTS = {
    "name": "Название способности. Например: Удар пепла, Восстание тьмы.",
    "type": "Тип способности: attack, strong_attack, control, support. Это строгое поле; если ввести другое, я переспрошу.",
    "limit": "Лимит использования. Обычно: at_will, 1/combat, 2/short_rest, 1/rest. Если ввести не из списка, поставлю at_will.",
    "range_shape": "Форма дистанции. Обычно: melee, ranged, touch, cone, line, sphere. Если ввести не из списка, поставлю melee.",
    "range_distance_m": "Дистанция в метрах. Например: 1.5, 6, 12. Если число не распознается, поставлю 1.",
    "bonus_ability": "Бонусная характеристика: str, dex, con, int, wis, cha. Если ввести не из списка, поставлю str.",
    "description": "Описание способности. Например: Клинок вспыхивает серым пламенем и обжигает цель.",
    "damage_dice": "Кость урона. Обычно: 1d4, 1d6, 2d6, 1d8. Если пусто или '-', поставлю 1d4.",
    "damage_type": "Тип урона. Обычно: slashing, piercing, bludgeoning, fire, cold, lightning, poison, acid, psychic, necrotic, radiant, thunder. Если не из списка, поставлю bludgeoning.",
    "control_type": "Тип контроля. Обычно: charm, blind, stun, fear, slow, silence, push, prone. Если не из списка, поставлю prone.",
    "duration_rounds": "Длительность контроля в раундах. Например: 1, 2, 3. Если число не распознается, поставлю 1.",
    "condition_end": "Условие окончания контроля. Например: До конца следующего хода цели.",
    "support_type": "Тип поддержки. Обычно: heal, buff_roll, buff_damage, buff_to_hit, extra_action, cleanse. Если не из списка, поставлю heal.",
    "check_dc": "Сложность проверки, если нужна. Например: 12. Если не нужна, введи '-'.",
    "check_attr": "Характеристика проверки: str, dex, con, int, wis, cha. Если не нужна, введи '-'.",
    "support_dice": "Кость лечения/усиления, если нужна. Например: 1d6. Если не нужна, введи '-'.",
    "action_type": "Тип действия, если способность дает действие: bonus_action, reaction, move. Если не нужно, введи '-'.",
    "cleanse_target": "Что снимает очищение: blind, fear, charm, stun, slow, silence, prone. Если не нужно, введи '-'.",
    "notes": "Заметки к поддержке. Если не нужны, введи '-'.",
}


async def show_character_list(message: Message, telegram_id: int, page: int = 0) -> None:
    async with async_session() as session:
        characters = await character_repository.list_by_user(
            session=session,
            telegram_id=telegram_id,
        )

    kb = character_list_kb(characters, page=page, action=CharacterAction.VIEW)
    await message.edit_text("Выбери персонажа:", reply_markup=kb)


async def show_character_card(call: CallbackQuery, character_id: int, page: int = 0) -> bool:
    async with async_session() as session:
        character_data = await character_repository.get_user_character_data(
            session=session,
            telegram_id=call.from_user.id,
            character_id=character_id,
        )

    if character_data is None:
        await call.answer("Персонаж не найден", show_alert=True)
        return False

    await call.message.edit_text(
        format_character_message(character_data),
        parse_mode=ParseMode.HTML,
        reply_markup=character_menu_kb(character_id, page=page),
    )
    return True


async def show_npc_list(message: Message, telegram_id: int, page: int = 0) -> None:
    async with async_session() as session:
        npcs = await npc_repository.list_by_user(
            session=session,
            telegram_id=telegram_id,
        )

    kb = npc_list_kb(npcs, page=page, action=NPCAction.VIEW)
    await message.edit_text("Выбери NPC:", reply_markup=kb)


async def show_npc_card(call: CallbackQuery, npc_id: int, page: int = 0) -> bool:
    async with async_session() as session:
        npc = await npc_repository.get_user_npc(
            session=session,
            telegram_id=call.from_user.id,
            npc_id=npc_id,
        )

    if npc is None:
        await call.answer("NPC не найден", show_alert=True)
        return False

    await call.message.edit_text(
        format_npc_message(npc),
        parse_mode=ParseMode.HTML,
        reply_markup=npc_menu_kb(npc_id, page=page),
    )
    return True


async def show_campaign_menu(call: CallbackQuery, campaign_id: int) -> bool:
    async with async_session() as session:
        campaign = await campaign_repository.get_user_campaign(
            session=session,
            telegram_id=call.from_user.id,
            campaign_id=campaign_id,
        )

    if campaign is None:
        await call.answer("Кампания не найдена или недоступна", show_alert=True)
        return False

    description = campaign.description or "Описание не указано"
    await call.message.edit_text(
        f"✅ Активная кампания: {campaign.title}\n\n{description}\n\nЧто открыть?",
        reply_markup=campaign_menu_kb(campaign.id),
    )
    return True


async def show_campaign_characters(call: CallbackQuery, campaign_id: int, page: int = 0) -> None:
    async with async_session() as session:
        campaign = await campaign_repository.get_user_campaign(
            session=session,
            telegram_id=call.from_user.id,
            campaign_id=campaign_id,
        )
        characters = await character_repository.list_by_campaign(
            session=session,
            telegram_id=call.from_user.id,
            campaign_id=campaign_id,
        )

    if campaign is None:
        await call.answer("Кампания не найдена или недоступна", show_alert=True)
        return

    if not characters:
        await call.message.edit_text(
            "В этой кампании пока нет прикреплённых персонажей.",
            reply_markup=campaign_menu_kb(campaign_id),
        )
        await call.answer()
        return

    await call.message.edit_text(
        f"Персонажи кампании: {campaign.title}",
        reply_markup=campaign_character_list_kb(campaign_id, characters, page=page),
    )
    await call.answer()


async def show_campaign_npcs(call: CallbackQuery, campaign_id: int, page: int = 0) -> None:
    async with async_session() as session:
        campaign = await campaign_repository.get_user_campaign(
            session=session,
            telegram_id=call.from_user.id,
            campaign_id=campaign_id,
        )
        npcs = await npc_repository.list_by_campaign(
            session=session,
            telegram_id=call.from_user.id,
            campaign_id=campaign_id,
        )

    if campaign is None:
        await call.answer("Кампания не найдена или недоступна", show_alert=True)
        return

    if not npcs:
        await call.message.edit_text(
            "В этой кампании пока нет прикреплённых NPC.",
            reply_markup=campaign_menu_kb(campaign_id),
        )
        await call.answer()
        return

    await call.message.edit_text(
        f"NPC кампании: {campaign.title}",
        reply_markup=campaign_npc_list_kb(campaign_id, npcs, page=page),
    )
    await call.answer()


async def ask_next_npc_step(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    step_index = data["step_index"]
    field = NPC_FIELDS[step_index]
    await message.answer(f"{step_index + 1}/{len(NPC_FIELDS)}. {NPC_FIELD_PROMPTS[field]}")


def get_ability_add_steps(ability_type: str | None = None) -> list[str]:
    steps = list(ABILITY_ADD_STEPS["common"])
    if ability_type in {"attack", "strong_attack"}:
        steps.extend(ABILITY_ADD_STEPS["damage"])
    elif ability_type == "control":
        steps.extend(ABILITY_ADD_STEPS["control"])
    elif ability_type == "support":
        steps.extend(ABILITY_ADD_STEPS["support"])
    return steps


def normalize_optional_value(value: str) -> str | None:
    text = value.strip()
    if text in {"", "-"}:
        return None
    return text


def build_ability_data(values: dict[str, str | None]) -> dict:
    ability_type = values.get("type") or "attack"
    data = {
        "name": values.get("name"),
        "type": ability_type,
        "limit": values.get("limit"),
        "range": {
            "shape": values.get("range_shape"),
            "distance_m": values.get("range_distance_m"),
        },
        "bonus_ability": values.get("bonus_ability"),
        "description": values.get("description"),
    }

    if ability_type in {"attack", "strong_attack"}:
        data["damage"] = {
            "dice": values.get("damage_dice"),
            "type": values.get("damage_type"),
        }
    elif ability_type == "control":
        data["control"] = {
            "type": values.get("control_type"),
            "duration_rounds": values.get("duration_rounds"),
            "condition_end": values.get("condition_end"),
        }
    elif ability_type == "support":
        data["support"] = {
            "type": values.get("support_type"),
            "check": {
                "dc": values.get("check_dc"),
                "dc_plus_attr": values.get("check_attr"),
            },
            "value": {
                "dice": values.get("support_dice"),
                "action": values.get("action_type"),
                "removes": [values["cleanse_target"]] if values.get("cleanse_target") else [],
            },
            "notes": values.get("notes"),
        }

    return data


async def ask_next_ability_step(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    steps = data["steps"]
    step_index = data["step_index"]
    step = steps[step_index]
    await message.answer(f"{step_index + 1}/{len(steps)}. {ABILITY_ADD_PROMPTS[step]}")
@router.message(CommandStart())
async def cmd_start (message: Message):
    try:
        async with async_session() as session:
            await user_repository.get_or_create_user(
                session=session,
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                display_name=message.from_user.full_name,
            )
            await session.commit()
    except Exception as e:
        await message.answer("Не получилось зарегистрировать пользователя в базе данных.")
        print(e)
        return

    await message.answer(
        "Привет!\nЭтот бот создан для помощи мастерам НРИ\n"
        "Доступные команды:\n/campaign_new\n/create_character\n/my_characters\n/create_npc\n/my_npcs\n/campaign_list\n/campaign_current\n/campaign_delete"
    )

#Создание кампании
@router.message(Command("help"))
async def cmd_help(message: Message):
    await cmd_start(message)


@router.message(Command("campaign_new"))
async def cmd_campaign_new(message: Message, state: FSMContext):
    await state.set_state(CreateCampaignStates.userGaveCampaignName)
    await message.answer("Напишите название кампании")

@router.message(CreateCampaignStates.userGaveCampaignName)
async def accept_company_name(message: Message, state: FSMContext):
    if await reject_command_as_input(message, state):
        return
    userCampaignName=message.text.strip()
    await state.update_data(campaign_name=userCampaignName)
    await state.set_state(CreateCampaignStates.userGaveCampaignDescription)
    await message.answer("Краткое описание вашей кампании")

@router.message(CreateCampaignStates.userGaveCampaignDescription)
async def accept_company_description(message: Message, state: FSMContext):
    if await reject_command_as_input(message, state):
        return
    user_campaign_description = message.text.strip()

    await state.update_data(campaign_description=user_campaign_description)
    data = await state.get_data()
    try:
        async with async_session() as session:
            await campaign_repository.create_campaign(
                session=session,
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                display_name=message.from_user.full_name,
                title=data["campaign_name"],
                description=data["campaign_description"],
            )
        await state.clear()
        await message.answer(
            "Кампания успешно создана✅\n"
            f"Название: {data['campaign_name']}\n"
            f"Описание: {data['campaign_description']}"
        )
    except Exception as e:
        await message.answer(
            "Не получилось создать кампанию. Ошибка при записи в базу данных."
        )
        print(e)
    
#Создание персонажа    
@router.message(Command('create_character'))
async def create_character(message: Message, state: FSMContext):
    await state.set_state(CreatecharacterStates.userGavePrompt)
    await message.answer("Напиши, каким ты хочешь видеть персонажа — раса, класс, характер, способность, бэкграунд…")

@router.message(CreatecharacterStates.userGavePrompt)
async def accept_character(message: Message, state: FSMContext):
    if await reject_command_as_input(message, state):
        return
    userPrompt = message.text.strip()
    thinking_msg = await message.answer_animation(animation=WAIT_MESSAGE_GIF_URL,caption="Думаю над персонажем…")
    try:
        result = await ask_llm(userPrompt, CREATE_CHARACTER_PROMPT)
        character_data = parse_character_response(result)
        async with async_session() as session:
            await character_repository.create_from_generated_data(
                session=session,
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                display_name=message.from_user.full_name,
                data=character_data,
            )
        text  = format_character_message(character_data)
    except Exception as e:
        await message.answer(f"Ошибка при создании персонажа: {e}")
        return
    await thinking_msg.delete()
    print("Персонаж сохранён в базу данных.")
    await message.answer(text, parse_mode=ParseMode.HTML)
    await state.clear()


@router.message(F.text == "Create NPC")
@router.message(F.text == "create npc")
@router.message(Command("create_npc", "CreateNPC", "npc_new"))
async def create_npc(message: Message, state: FSMContext):
    await state.set_state(CreateNPCStates.waiting_for_value)
    await state.update_data(step_index=0, values={})
    await message.answer(
        "Создаём NPC вручную. В свободных текстовых полях можно писать что угодно; чтобы оставить поле пустым, отправь '-'."
    )
    await ask_next_npc_step(message, state)


@router.message(CreateNPCStates.waiting_for_value)
async def accept_npc_value(message: Message, state: FSMContext):
    if message.text is None:
        await message.answer("Пришли значение текстом.")
        return

    if await reject_command_as_input(message, state):
        return

    data = await state.get_data()
    step_index = data["step_index"]
    field = NPC_FIELDS[step_index]
    values = data.get("values") or {}
    values[field] = message.text.strip()

    step_index += 1
    await state.update_data(step_index=step_index, values=values)

    if step_index < len(NPC_FIELDS):
        await ask_next_npc_step(message, state)
        return

    try:
        async with async_session() as session:
            npc = await npc_repository.create_for_user(
                session=session,
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                display_name=message.from_user.full_name,
                data=values,
            )
    except Exception as e:
        await message.answer("Не получилось создать NPC. Ошибка при работе с базой данных.")
        print(e)
        await state.clear()
        return

    await state.clear()
    await message.answer(
        "NPC создан:",
    )
    await message.answer(
        format_npc_message(npc),
        parse_mode=ParseMode.HTML,
        reply_markup=npc_menu_kb(npc.id),
    )


@router.message(Command("my_npcs", "npc_list", "npcs"))
async def cmd_my_npcs(message: Message):
    try:
        async with async_session() as session:
            npcs = await npc_repository.list_by_user(
                session=session,
                telegram_id=message.from_user.id,
            )
    except Exception as e:
        await message.answer("Не получилось получить NPC. Ошибка при работе с базой данных.")
        print(e)
        return

    if not npcs:
        await message.answer("У тебя пока нет NPC. Создай: /create_npc")
        return

    kb = npc_list_kb(npcs, page=0, action=NPCAction.VIEW)
    await message.answer("Выбери NPC:", reply_markup=kb)


@router.callback_query(NPCCB.filter())
async def cb_npc_list(call: CallbackQuery, callback_data: NPCCB):
    try:
        async with async_session() as session:
            npcs = await npc_repository.list_by_user(
                session=session,
                telegram_id=call.from_user.id,
            )
    except Exception as e:
        await call.answer("Не смог получить список NPC", show_alert=True)
        print(e)
        return

    if callback_data.npc_id == 0:
        kb = npc_list_kb(
            npcs,
            action=NPCAction(callback_data.action),
            page=callback_data.page,
        )
        await call.message.edit_reply_markup(reply_markup=kb)
        await call.answer()
        return

    try:
        async with async_session() as session:
            npc = await npc_repository.get_user_npc(
                session=session,
                telegram_id=call.from_user.id,
                npc_id=callback_data.npc_id,
            )
    except Exception as e:
        await call.answer("Не смог открыть NPC", show_alert=True)
        print(e)
        return

    if npc is None:
        await call.answer("NPC не найден", show_alert=True)
        return

    await call.message.edit_text(
        format_npc_message(npc),
        parse_mode=ParseMode.HTML,
        reply_markup=npc_menu_kb(callback_data.npc_id, page=callback_data.page),
    )
    await call.answer()


@router.callback_query(NPCMenuCB.filter())
async def cb_npc_actions(call: CallbackQuery, callback_data: NPCMenuCB):
    if callback_data.action == "back":
        try:
            await show_npc_list(
                message=call.message,
                telegram_id=call.from_user.id,
                page=callback_data.page,
            )
        except Exception as e:
            await call.answer("Не смог вернуться к списку NPC", show_alert=True)
            print(e)
            return
        await call.answer()
        return

    if callback_data.action == "view":
        try:
            shown = await show_npc_card(call, callback_data.npc_id, page=callback_data.page)
        except Exception as e:
            await call.answer("Не смог открыть NPC", show_alert=True)
            print(e)
            return
        if shown:
            await call.answer()
        return

    if callback_data.action == "edit":
        await call.message.edit_text(
            "Что меняем?",
            reply_markup=npc_edit_fields_kb(callback_data.npc_id),
        )
        await call.answer()
        return

    if callback_data.action == "attach":
        try:
            async with async_session() as session:
                campaigns = await campaign_repository.get_user_campaigns(
                    session=session,
                    telegram_id=call.from_user.id,
                )
        except Exception as e:
            await call.answer("Не смог получить список кампаний", show_alert=True)
            print(e)
            return

        if not campaigns:
            await call.message.edit_text(
                "У тебя пока нет кампаний, к которым можно прикрепить NPC. Создай кампанию: /campaign_new",
                reply_markup=npc_menu_kb(callback_data.npc_id, page=callback_data.page),
            )
            await call.answer()
            return

        await call.message.edit_text(
            "К какой кампании прикрепить NPC?",
            reply_markup=npc_campaigns_kb(callback_data.npc_id, campaigns, page=0),
        )
        await call.answer()


@router.callback_query(NPCEditCB.filter())
async def cb_npc_edit(call: CallbackQuery, callback_data: NPCEditCB, state: FSMContext):
    field = callback_data.field
    label = NPC_FIELD_LABELS.get(field, field)
    hint = NPC_FIELD_HINTS.get(field)

    await state.set_state(EditNPCStates.waiting_for_value)
    await state.update_data(npc_id=callback_data.npc_id, field=field)

    text = f"Введи новое значение для поля: {label}. Чтобы оставить пустым, отправь '-'."
    if hint:
        text += f"\n{hint}"
    await call.message.edit_text(text)
    await call.answer()


@router.message(EditNPCStates.waiting_for_value)
async def accept_npc_edit_value(message: Message, state: FSMContext):
    if message.text is None:
        await message.answer("Пришли новое значение текстом.")
        return

    if await reject_command_as_input(message, state):
        return

    data = await state.get_data()
    npc_id = data["npc_id"]
    field = data["field"]
    value = message.text.strip()

    try:
        async with async_session() as session:
            npc = await npc_repository.update_field(
                session=session,
                telegram_id=message.from_user.id,
                npc_id=npc_id,
                field=field,
                value=value,
            )
    except Exception as e:
        await message.answer("Не получилось сохранить изменение. Ошибка при работе с базой данных.")
        print(e)
        await state.clear()
        return

    await state.clear()

    if npc is None:
        await message.answer("Не получилось найти NPC или выбранное поле.")
        return

    await message.answer("Готово. Обновлённая карточка NPC:")
    await message.answer(
        format_npc_message(npc),
        parse_mode=ParseMode.HTML,
        reply_markup=npc_menu_kb(npc_id),
    )


@router.callback_query(NPCCampaignCB.filter())
async def cb_attach_npc_to_campaign(call: CallbackQuery, callback_data: NPCCampaignCB):
    try:
        async with async_session() as session:
            campaigns = await campaign_repository.get_user_campaigns(
                session=session,
                telegram_id=call.from_user.id,
            )
    except Exception as e:
        await call.answer("Не смог получить список кампаний", show_alert=True)
        print(e)
        return

    if callback_data.campaign_id == 0:
        await call.message.edit_text(
            "К какой кампании прикрепить NPC?",
            reply_markup=npc_campaigns_kb(
                callback_data.npc_id,
                campaigns,
                page=callback_data.page,
            ),
        )
        await call.answer()
        return

    try:
        async with async_session() as session:
            npc = await npc_repository.attach_to_campaign(
                session=session,
                telegram_id=call.from_user.id,
                npc_id=callback_data.npc_id,
                campaign_id=callback_data.campaign_id,
            )
    except Exception as e:
        await call.answer("Не получилось прикрепить NPC", show_alert=True)
        print(e)
        return

    if npc is None:
        await call.answer("NPC или кампания не найдены", show_alert=True)
        return

    await call.message.edit_text(
        "NPC прикреплён к кампании.",
        reply_markup=npc_menu_kb(callback_data.npc_id),
    )
    await call.answer("Готово")

#Список кампаний
@router.message(Command("my_characters", "MyCharacters", "characters"))
async def cmd_my_characters(message: Message):
    try:
        async with async_session() as session:
            characters = await character_repository.list_by_user(
                session=session,
                telegram_id=message.from_user.id,
            )
    except Exception as e:
        await message.answer(
            "Не получилось получить персонажей. Ошибка при работе с базой данных."
        )
        print(e)
        return

    if not characters:
        await message.answer("У тебя пока нет персонажей. Создай: /create_character")
        return

    kb = character_list_kb(characters, page=0, action=CharacterAction.VIEW)
    await message.answer("Выбери персонажа:", reply_markup=kb)


@router.callback_query(CharacterCB.filter())
async def cb_character_menu(call: CallbackQuery, callback_data: CharacterCB):
    try:
        async with async_session() as session:
            characters = await character_repository.list_by_user(
                session=session,
                telegram_id=call.from_user.id,
            )
    except Exception as e:
        await call.answer("Не смог получить список персонажей", show_alert=True)
        print(e)
        return

    if callback_data.character_id == 0:
        kb = character_list_kb(
            characters,
            action=CharacterAction(callback_data.action),
            page=callback_data.page,
        )
        await call.message.edit_reply_markup(reply_markup=kb)
        await call.answer()
        return

    try:
        async with async_session() as session:
            character_data = await character_repository.get_user_character_data(
                session=session,
                telegram_id=call.from_user.id,
                character_id=callback_data.character_id,
            )
    except Exception as e:
        await call.answer("Не смог открыть персонажа", show_alert=True)
        print(e)
        return

    if character_data is None:
        await call.answer("Персонаж не найден", show_alert=True)
        return

    await call.message.edit_text(
        format_character_message(character_data),
        parse_mode=ParseMode.HTML,
        reply_markup=character_menu_kb(callback_data.character_id, page=callback_data.page),
    )
    await call.answer()


@router.callback_query(CharacterMenuCB.filter())
async def cb_character_actions(call: CallbackQuery, callback_data: CharacterMenuCB):
    if callback_data.action == "back":
        try:
            await show_character_list(
                message=call.message,
                telegram_id=call.from_user.id,
                page=callback_data.page,
            )
        except Exception as e:
            await call.answer("Не смог вернуться к списку персонажей", show_alert=True)
            print(e)
            return
        await call.answer()
        return

    if callback_data.action == "view":
        try:
            shown = await show_character_card(call, callback_data.character_id, page=callback_data.page)
        except Exception as e:
            await call.answer("Не смог открыть персонажа", show_alert=True)
            print(e)
            return
        if shown:
            await call.answer()
        return

    if callback_data.action == "edit":
        await call.message.edit_text(
            "Что меняем?",
            reply_markup=character_edit_sections_kb(callback_data.character_id, page=callback_data.page),
        )
        await call.answer()
        return

    if callback_data.action == "attach":
        try:
            async with async_session() as session:
                campaigns = await campaign_repository.get_user_campaigns(
                    session=session,
                    telegram_id=call.from_user.id,
                )
        except Exception as e:
            await call.answer("Не смог получить список кампаний", show_alert=True)
            print(e)
            return

        if not campaigns:
            await call.message.edit_text(
                "У тебя пока нет кампаний, к которым можно присоединить персонажа. Создай кампанию: /campaign_new",
                reply_markup=character_menu_kb(callback_data.character_id, page=callback_data.page),
            )
            await call.answer()
            return

        await call.message.edit_text(
            "К какой кампании прикрепить персонажа? Если персонаж уже был в кампании, привязка будет заменена.",
            reply_markup=character_campaigns_kb(callback_data.character_id, campaigns, page=0),
        )
        await call.answer()


@router.callback_query(CharacterEditCB.filter())
async def cb_character_edit(call: CallbackQuery, callback_data: CharacterEditCB, state: FSMContext):
    scope = EDIT_SCOPE_CODES.get(callback_data.scope, callback_data.scope)
    field = EDIT_FIELD_CODES.get(callback_data.field, callback_data.field)

    if scope == "section":
        if field == "abilities":
            try:
                async with async_session() as session:
                    abilities = await character_repository.list_character_abilities(
                        session=session,
                        telegram_id=call.from_user.id,
                        character_id=callback_data.character_id,
                    )
            except Exception as e:
                await call.answer("Не смог получить способности", show_alert=True)
                print(e)
                return

            await call.message.edit_text(
                "Выбери способность или добавь новую:",
                reply_markup=character_abilities_kb(callback_data.character_id, abilities),
            )
            await call.answer()
            return

        await call.message.edit_text(
            "Выбери поле:",
            reply_markup=character_edit_fields_kb(callback_data.character_id, field),
        )
        await call.answer()
        return

    if scope == "ability_select":
        await call.message.edit_text(
            "Что меняем в способности?",
            reply_markup=ability_edit_fields_kb(callback_data.character_id, callback_data.ability_id),
        )
        await call.answer()
        return

    if scope == "add_ability":
        await state.set_state(AddAbilityStates.waiting_for_value)
        await state.update_data(
            character_id=callback_data.character_id,
            steps=get_ability_add_steps(),
            step_index=0,
            values={},
        )
        await call.answer()
        await call.message.answer("Создаём новую способность. На необязательных полях можно отправить '-'.")
        await ask_next_ability_step(call.message, state)
        return

    if scope == "delete_ability":
        if field == "ask":
            await call.message.edit_text(
                "Удалить эту способность? Действие нельзя будет отменить.",
                reply_markup=delete_ability_confirm_kb(callback_data.character_id, callback_data.ability_id),
            )
            await call.answer()
            return

        if field == "yes":
            try:
                async with async_session() as session:
                    ok = await character_repository.delete_ability_for_user(
                        session=session,
                        telegram_id=call.from_user.id,
                        character_id=callback_data.character_id,
                        ability_id=callback_data.ability_id,
                    )
                    abilities = await character_repository.list_character_abilities(
                        session=session,
                        telegram_id=call.from_user.id,
                        character_id=callback_data.character_id,
                    )
            except Exception as e:
                await call.answer("Не получилось удалить способность", show_alert=True)
                print(e)
                return

            if not ok:
                await call.answer("Способность не найдена", show_alert=True)
                return

            await call.message.edit_text(
                "Способность удалена. Выбери следующую или добавь новую:",
                reply_markup=character_abilities_kb(callback_data.character_id, abilities),
            )
            await call.answer("Удалено")
            return

    if scope not in {"character", "ability"}:
        await call.answer("Неизвестное действие", show_alert=True)
        return

    label_map = CHARACTER_FIELD_LABELS if scope == "character" else ABILITY_FIELD_LABELS
    label = label_map.get(field, field)
    hint = FIELD_HINTS.get(field)

    await state.set_state(EditCharacterStates.waiting_for_value)
    await state.update_data(
        edit_scope=scope,
        character_id=callback_data.character_id,
        ability_id=callback_data.ability_id,
        field=field,
    )

    text = f"Введи новое значение для поля: {label}."
    if hint:
        text += f"\n{hint}"
    await call.message.edit_text(text)
    await call.answer()


@router.message(EditCharacterStates.waiting_for_value)
async def accept_character_edit_value(message: Message, state: FSMContext):
    data = await state.get_data()
    if not message.text:
        await message.answer("Пришли новое значение текстом.")
        return

    if await reject_command_as_input(message, state):
        return

    value = message.text.strip()
    scope = data["edit_scope"]
    character_id = data["character_id"]
    field = data["field"]

    try:
        async with async_session() as session:
            if scope == "character":
                updated = await character_repository.update_character_field(
                    session=session,
                    telegram_id=message.from_user.id,
                    character_id=character_id,
                    field=field,
                    value=value,
                )
            else:
                updated = await character_repository.update_ability_field(
                    session=session,
                    telegram_id=message.from_user.id,
                    character_id=character_id,
                    ability_id=data["ability_id"],
                    field=field,
                    value=value,
                )

            character_data = await character_repository.get_user_character_data(
                session=session,
                telegram_id=message.from_user.id,
                character_id=character_id,
            )
    except Exception as e:
        await message.answer("Не получилось сохранить изменение. Ошибка при работе с базой данных.")
        print(e)
        await state.clear()
        return

    await state.clear()

    if updated is None or character_data is None:
        await message.answer("Не получилось найти персонажа или выбранное поле.")
        return

    await message.answer(
        "Готово. Обновлённая карточка персонажа:",
    )
    await message.answer(
        format_character_message(character_data),
        parse_mode=ParseMode.HTML,
        reply_markup=character_menu_kb(character_id),
    )


@router.message(AddAbilityStates.waiting_for_value)
async def accept_add_ability_value(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Пришли значение текстом.")
        return

    if await reject_command_as_input(message, state):
        return

    data = await state.get_data()
    steps = data["steps"]
    step_index = data["step_index"]
    step = steps[step_index]
    values = data.get("values") or {}
    value = normalize_optional_value(message.text)

    if step == "type" and value not in {"attack", "strong_attack", "control", "support"}:
        await message.answer("Такого типа способности нет. Введи один из вариантов: attack, strong_attack, control, support.")
        return

    values[step] = value

    if step == "type":
        steps = get_ability_add_steps(value)

    step_index += 1
    await state.update_data(steps=steps, step_index=step_index, values=values)

    if step_index < len(steps):
        await ask_next_ability_step(message, state)
        return

    character_id = data["character_id"]
    ability_data = build_ability_data(values)

    try:
        async with async_session() as session:
            ability = await character_repository.create_ability_for_user(
                session=session,
                telegram_id=message.from_user.id,
                character_id=character_id,
                ability_data=ability_data,
            )
            character_data = await character_repository.get_user_character_data(
                session=session,
                telegram_id=message.from_user.id,
                character_id=character_id,
            )
    except Exception as e:
        await message.answer("Не получилось создать способность. Ошибка при работе с базой данных.")
        print(e)
        await state.clear()
        return

    await state.clear()

    if ability is None or character_data is None:
        await message.answer("Не получилось найти персонажа для добавления способности.")
        return

    await message.answer("Способность добавлена. Обновлённая карточка персонажа:")
    await message.answer(
        format_character_message(character_data),
        parse_mode=ParseMode.HTML,
        reply_markup=character_menu_kb(character_id),
    )


@router.callback_query(CharacterCampaignCB.filter())
async def cb_attach_character_to_campaign(call: CallbackQuery, callback_data: CharacterCampaignCB):
    try:
        async with async_session() as session:
            campaigns = await campaign_repository.get_user_campaigns(
                session=session,
                telegram_id=call.from_user.id,
            )
    except Exception as e:
        await call.answer("Не смог получить список кампаний", show_alert=True)
        print(e)
        return

    if callback_data.campaign_id == 0:
        await call.message.edit_text(
            "К какой кампании прикрепить персонажа? Если персонаж уже был в кампании, привязка будет заменена.",
            reply_markup=character_campaigns_kb(
                callback_data.character_id,
                campaigns,
                page=callback_data.page,
            ),
        )
        await call.answer()
        return

    if callback_data.campaign_id == -1:
        try:
            async with async_session() as session:
                ok = await character_repository.detach_from_campaign(
                    session=session,
                    telegram_id=call.from_user.id,
                    character_id=callback_data.character_id,
                )
        except Exception as e:
            await call.answer("Не получилось открепить персонажа от кампании", show_alert=True)
            print(e)
            return

        if not ok:
            await call.answer("Персонаж не найден или нет прав", show_alert=True)
            return

        await call.message.edit_text(
            "✅ Персонаж откреплён от кампании и теперь доступен как свободный.",
            reply_markup=character_menu_kb(callback_data.character_id),
        )
        await call.answer("Готово")
        return

    try:
        async with async_session() as session:
            ok = await character_repository.attach_to_campaign(
                session=session,
                telegram_id=call.from_user.id,
                character_id=callback_data.character_id,
                campaign_id=callback_data.campaign_id,
            )
    except Exception as e:
        await call.answer("Не получилось присоединить персонажа", show_alert=True)
        print(e)
        return

    if not ok:
        await call.answer("Персонаж или кампания не найдены", show_alert=True)
        return

    await call.message.edit_text(
        "✅ Персонаж прикреплён к выбранной кампании.",
        reply_markup=character_menu_kb(callback_data.character_id),
    )
    await call.answer("Готово")

@router.message(Command("campaign_list"))
async def cmd_campaign_list(message: Message):
    try:
        async with async_session() as session:
            campaigns = await campaign_repository.get_user_campaigns(
                session=session,
                telegram_id=message.from_user.id,
            )
    except Exception as e:
        await message.answer(
            "Не получилось получить кампанию. Ошибка при работе с в базой данных."
        )
        print(e)

    if not campaigns:
        await message.answer("У тебя пока нет кампаний. Создай: /campaign_new")
        return

    kb = campaign_list_kb(campaigns, page=0, action=CampaignAction.SELECT)
    await message.answer("Выбери кампанию:", reply_markup=kb)

@router.callback_query(CampaignCB.filter())
async def cb_campaign_menu(call: CallbackQuery, callback_data: CampaignCB):
    action = CampaignAction(callback_data.action)  # строка -> Enum
    try:
        async with async_session() as session:
            campaigns = await campaign_repository.get_user_campaigns(
                session=session,
                telegram_id=call.from_user.id,
            )
    except Exception as e:
        print(e)

    # Навигация (campaign_id == 0)
    if callback_data.campaign_id == 0:
        kb = campaign_list_kb(campaigns, action=action, page=callback_data.page)
        await call.message.edit_reply_markup(reply_markup=kb)
        await call.answer()
        return

    # Нажали на конкретную кампанию
    campaign_id = callback_data.campaign_id

    if action == CampaignAction.SELECT:
        try:
            async with async_session() as session:
                campaign = await campaign_repository.get_user_campaign(
                    session=session,
                    telegram_id=call.from_user.id,
                    campaign_id=campaign_id,
                )
                ok = False
                if campaign is not None:
                    ok = await user_repository.set_active_campaign_to_user(
                        session=session,
                        telegram_id=call.from_user.id,
                        active_campaign_id=campaign_id,
                    )
        except Exception as e:
            await call.answer(
                "Не получилось выюрать кампанию кампанию. Ошибка при работе с в базой данных."
            )
            print(e)
            return
        if ok:
            await call.answer("Выбрано")
            await show_campaign_menu(call, campaign_id)
        else:
            await call.answer("Кампания не найдена или недоступна", show_alert=True)
        return

    if action == CampaignAction.DELETE:
        try:
            async with async_session() as session:
                ok = await campaign_repository.delete_campaign_by_owner(
                    session=session,
                    telegram_id=call.from_user.id,
                    campaign_id=campaign_id
                )
        except Exception as e:
            print(e)
        if not ok:
            await call.answer("Не нашёл кампанию", show_alert=True)
            return

        # после удаления — показать обновлённый список (и корректную страницу)
        try:
            async with async_session() as session:
                campaigns = await campaign_repository.get_user_campaigns(
                    session=session,
                    telegram_id=call.from_user.id,
                )
        except Exception as e:
            print(e)
        if campaigns ==[]:
             await call.message.edit_text("У вас больше не осталлось кампаний")
             await call.answer("Удалено")
             return
        kb = campaign_list_kb(campaigns, action=action, page=min(callback_data.page, max(0, (len(campaigns)-1)//PAGE_SIZE)))
        await call.message.edit_text("🗑 Кампания удалена. Выбери следующую:", reply_markup=kb)
        await call.answer("Удалено")
        return


@router.callback_query(CampaignMenuCB.filter())
async def cb_campaign_panel(call: CallbackQuery, callback_data: CampaignMenuCB, state: FSMContext):
    if callback_data.action == "back":
        try:
            async with async_session() as session:
                campaigns = await campaign_repository.get_user_campaigns(
                    session=session,
                    telegram_id=call.from_user.id,
                )
        except Exception as e:
            await call.answer("Не смог получить список кампаний", show_alert=True)
            print(e)
            return

        if not campaigns:
            await call.message.edit_text("У тебя пока нет кампаний. Создай: /campaign_new")
            await call.answer()
            return

        await call.message.edit_text(
            "Выбери кампанию:",
            reply_markup=campaign_list_kb(campaigns, action=CampaignAction.SELECT, page=callback_data.page),
        )
        await call.answer()
        return

    if callback_data.action == "view":
        try:
            shown = await show_campaign_menu(call, callback_data.campaign_id)
        except Exception as e:
            await call.answer("Не смог открыть кампанию", show_alert=True)
            print(e)
            return
        if shown:
            await call.answer()
        return

    if callback_data.action == "characters":
        try:
            await show_campaign_characters(call, callback_data.campaign_id, page=callback_data.page)
        except Exception as e:
            await call.answer("Не смог получить персонажей кампании", show_alert=True)
            print(e)
        return

    if callback_data.action == "npcs":
        try:
            await show_campaign_npcs(call, callback_data.campaign_id, page=callback_data.page)
        except Exception as e:
            await call.answer("Не смог получить NPC кампании", show_alert=True)
            print(e)
        return

    if callback_data.action == "invite":
        try:
            async with async_session() as session:
                can_invite = await campaign_repository.can_user_manage_campaign_members(
                    session=session,
                    telegram_id=call.from_user.id,
                    campaign_id=callback_data.campaign_id,
                )
        except Exception as e:
            await call.answer("Не смог проверить права на кампанию", show_alert=True)
            print(e)
            return

        if not can_invite:
            await call.answer("Приглашать игроков могут только владелец или гейммастер", show_alert=True)
            return

        await state.set_state(InviteCampaignMemberStates.waiting_for_username)
        await state.update_data(campaign_id=callback_data.campaign_id)
        await call.message.edit_text(
            "Отправь username пользователя, которого нужно пригласить. Например: @username.\n\n"
            "Важно: пользователь должен хотя бы раз нажать /start в этом боте."
        )
        await call.answer()
        return

    await call.answer("Неизвестное действие", show_alert=True)


@router.message(InviteCampaignMemberStates.waiting_for_username)
async def accept_campaign_invite_username(message: Message, state: FSMContext):
    if await reject_command_as_input(message, state):
        return

    target_username = (message.text or "").strip().lstrip("@")
    if not target_username:
        await message.answer("Отправь username пользователя. Например: @username.")
        return

    if not target_username.replace("_", "").isalnum() or len(target_username) > 32:
        await message.answer("Username должен выглядеть как @username. Отправь username ещё раз.")
        return

    if message.from_user.username and target_username.casefold() == message.from_user.username.casefold():
        await message.answer("Себя приглашать не нужно: ты уже участник этой кампании.")
        await state.clear()
        return

    data = await state.get_data()
    campaign_id = data.get("campaign_id")
    if campaign_id is None:
        await state.clear()
        await message.answer("Не нашёл кампанию для приглашения. Открой кампанию заново через /campaign_list.")
        return

    try:
        async with async_session() as session:
            can_invite = await campaign_repository.can_user_manage_campaign_members(
                session=session,
                telegram_id=message.from_user.id,
                campaign_id=campaign_id,
            )
            target_user = await user_repository.get_by_username(
                session=session,
                username=target_username,
            )
    except Exception as e:
        await message.answer("Не получилось проверить пользователя в базе данных.")
        print(e)
        return

    if not can_invite:
        await state.clear()
        await message.answer("У тебя нет прав приглашать игроков в эту кампанию.")
        return

    if target_user is None:
        await message.answer(
            "Я ещё не знаю такого пользователя. Попроси его нажать /start в этом боте, потом повтори приглашение."
        )
        return

    await state.clear()
    await message.answer(
        "Выбери роль пользователя в кампании:",
        reply_markup=campaign_invite_role_kb(campaign_id, target_username),
    )


@router.callback_query(CampaignInviteRoleCB.filter())
async def cb_campaign_invite_role(call: CallbackQuery, callback_data: CampaignInviteRoleCB):
    role_labels = {
        "gm": "Гейммастер",
        "player": "Игрок",
        "viewer": "Наблюдатель",
    }

    try:
        async with async_session() as session:
            member = await campaign_repository.invite_registered_user(
                session=session,
                inviter_telegram_id=call.from_user.id,
                campaign_id=callback_data.campaign_id,
                target_username=callback_data.username,
                role=callback_data.role,
            )
    except Exception as e:
        await call.answer("Не получилось пригласить пользователя", show_alert=True)
        print(e)
        return

    if member is None:
        await call.answer("Нет прав, пользователь не найден или роль недоступна", show_alert=True)
        return

    await call.message.edit_text(
        f"Пользователь @{callback_data.username} добавлен в кампанию.\n"
        f"Роль: {role_labels.get(member.role, member.role)}",
        reply_markup=campaign_menu_kb(callback_data.campaign_id),
    )
    await call.answer("Готово")


@router.callback_query(CampaignEntityCB.filter())
async def cb_campaign_entity(call: CallbackQuery, callback_data: CampaignEntityCB):
    if callback_data.entity == "ch":
        if callback_data.entity_id == 0 or callback_data.action == "p":
            try:
                await show_campaign_characters(call, callback_data.campaign_id, page=callback_data.page)
            except Exception as e:
                await call.answer("Не смог получить персонажей кампании", show_alert=True)
                print(e)
            return

        try:
            async with async_session() as session:
                character_data = await character_repository.get_campaign_character_data(
                    session=session,
                    telegram_id=call.from_user.id,
                    campaign_id=callback_data.campaign_id,
                    character_id=callback_data.entity_id,
                )
        except Exception as e:
            await call.answer("Не смог открыть персонажа", show_alert=True)
            print(e)
            return

        if character_data is None:
            await call.answer("Персонаж не найден в этой кампании", show_alert=True)
            return

        await call.message.edit_text(
            format_character_message(character_data),
            parse_mode=ParseMode.HTML,
            reply_markup=character_menu_kb(callback_data.entity_id, page=callback_data.page),
        )
        await call.answer()
        return

    if callback_data.entity == "npc":
        if callback_data.entity_id == 0 or callback_data.action == "p":
            try:
                await show_campaign_npcs(call, callback_data.campaign_id, page=callback_data.page)
            except Exception as e:
                await call.answer("Не смог получить NPC кампании", show_alert=True)
                print(e)
            return

        try:
            async with async_session() as session:
                npc = await npc_repository.get_campaign_npc(
                    session=session,
                    telegram_id=call.from_user.id,
                    campaign_id=callback_data.campaign_id,
                    npc_id=callback_data.entity_id,
                )
        except Exception as e:
            await call.answer("Не смог открыть NPC", show_alert=True)
            print(e)
            return

        if npc is None:
            await call.answer("NPC не найден в этой кампании", show_alert=True)
            return

        await call.message.edit_text(
            format_npc_message(npc),
            parse_mode=ParseMode.HTML,
            reply_markup=npc_menu_kb(callback_data.entity_id, page=callback_data.page),
        )
        await call.answer()
        return

    await call.answer("Неизвестный раздел", show_alert=True)


@router.callback_query(F.data == "noop")

async def cb_noop(call: CallbackQuery):
    await call.answer()

@router.callback_query(F.data == "close")
async def cb_close(call: CallbackQuery):
    await call.message.delete()
    await call.answer()

#Текущая кампания
@router.message(Command("campaign_current"))
async def cmd_campaign_list(message: Message):
    try:
        async with async_session() as session:
            current_campaign = await user_repository.get_current_campaign(
                session=session,
                telegram_id=message.from_user.id
            )
    except Exception as e:
        await message.answer(
            "Не получилось получить кампанию. Ошибка при работе с в базой данных."
        )
        print(e)
    if current_campaign == None:
        await message.answer('На данный момент у вас нет выбранной кампании\nВы можете выбрать её использовав команду /campaign_list или создать новую командой /campaign_new')
    else:await message.answer(f'Текущая кампания: {current_campaign.title}\nОписание: {current_campaign.description}')

#Удаление
@router.message(Command("campaign_delete"))
async def cmd_campaign_delete(message: Message):
    try:
        async with async_session() as session:
            campaigns = await campaign_repository.get_user_campaigns(
                session=session,
                telegram_id=message.from_user.id,
            )
    except Exception as e:
        await message.answer(
            "Не получилось получить кампанию. Ошибка при работе с в базой данных."
        )
        print(e)
    if not campaigns:
        await message.answer("Удалять нечего — кампаний нет.")
        return

    kb = campaign_list_kb(campaigns, action=CampaignAction.DELETE, page=0)
    await message.answer("Выбери кампанию, которую хочешь удалить:", reply_markup=kb)
