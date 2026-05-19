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
from app.keyboards.compaignKB import*
from app.repos.memory_campaign_repo import*
from app.llm_client import ask_llm
from app.prompts import*
from db.repositories.user_repository import UserRepository
from db.repositories.campaign_repository import CampaignRepository
from db.repositories.character_repository import CharacterRepository

router = Router()
campaign_repo = InMemoryCampaignRepo()
campaign_repository = CampaignRepository()
user_repository = UserRepository()
character_repository = CharacterRepository()

WAIT_MESSAGE_GIF_URL="https://media1.tenor.com/m/OuPsTzfoh6cAAAAd/%D1%82%D0%B0%D0%BA%D0%B8%D0%B7%D0%B0%D0%BF%D0%B8%D1%88%D0%B5%D0%BC-%D0%B7%D0%B0%D0%BF%D0%B8%D1%88%D0%B5%D0%BC.gif"

class CreatecharacterStates(StatesGroup):
    userGavePrompt = State()

class EditCharacterStates(StatesGroup):
    waiting_for_value = State()

class AddAbilityStates(StatesGroup):
    waiting_for_value = State()

class CreateCampaignStates(StatesGroup):
    userGaveCampaignName = State()
    userGaveCampaignDescription = State()


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
    "gender": "Допустимые значения: male, female, other.",
    "usage_limit": "Допустимые значения: at_will, 1/combat, 2/short_rest, 1/rest.",
    "range_shape": "Допустимые значения: touch, melee, ranged, cone, line, sphere.",
    "bonus_ability": "Допустимые значения: str, dex, con, int, wis, cha.",
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
    await message.answer(
        "Привет!\nЭтот бот создан для помощи мастерам НРИ\n"
        "Доступные команды:\n/campaign_new\n/create_character\n/my_characters\n/campaign_list\n/campaign_current\n/campaign_delete"
    )

#Создание кампании
@router.message(Command("campaign_new"))
async def cmd_start (message: Message, state: FSMContext):
    await state.set_state(CreateCampaignStates.userGaveCampaignName)
    await message.answer("Напишите название кампании")

@router.message(CreateCampaignStates.userGaveCampaignName)
async def accept_company_name(message: Message, state: FSMContext):
    userCampaignName=message.text.strip()
    await state.update_data(campaign_name=userCampaignName)
    await state.set_state(CreateCampaignStates.userGaveCampaignDescription)
    await message.answer("Краткое описание вашей кампании")

@router.message(CreateCampaignStates.userGaveCampaignDescription)
async def accept_company_description(message: Message, state: FSMContext):
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
            "В какую кампанию добавить персонажа?",
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
            "В какую кампанию добавить персонажа?",
            reply_markup=character_campaigns_kb(
                callback_data.character_id,
                campaigns,
                page=callback_data.page,
            ),
        )
        await call.answer()
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
        "✅ Персонаж присоединён к кампании.",
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
                ok = await user_repository.set_active_campaign_to_user(
                    session=session,
                    telegram_id=call.from_user.id,
                    active_campaign_id=campaign_id
                )
        except Exception as e:
            await call.answer(
                "Не получилось выюрать кампанию кампанию. Ошибка при работе с в базой данных."
            )
            print(e)
        if ok:
            await call.answer("Выбрано")
            await call.message.edit_text("✅ Кампания выбрана")
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
