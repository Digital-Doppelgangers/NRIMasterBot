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

router = Router()
campaign_repo = InMemoryCampaignRepo()
campaign_repository = CampaignRepository()
user_repository = UserRepository()

WAIT_MESSAGE_GIF_URL="https://media1.tenor.com/m/OuPsTzfoh6cAAAAd/%D1%82%D0%B0%D0%BA%D0%B8%D0%B7%D0%B0%D0%BF%D0%B8%D1%88%D0%B5%D0%BC-%D0%B7%D0%B0%D0%BF%D0%B8%D1%88%D0%B5%D0%BC.gif"

class CreatecharacterStates(StatesGroup):
    userGavePrompt = State()

class CreateCampaignStates(StatesGroup):
    userGaveCampaignName = State()
    userGaveCampaignDescription = State()
@router.message(CommandStart())
async def cmd_start (message: Message):
    await message.answer(
        "Привет!\nЭтот бот создан для помощи мастерам НРИ\n"
        "Доступные команды:\n/campaign_new\n/create_character\n/campaign_list\n/campaign_current\n/campaign_delete"
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
        text  = format_character_message(character_data)
    except Exception as e:
        await message.answer(f"Ошибка при обращении к модели: {e}")
        return
    await thinking_msg.delete()
    await message.answer(text, parse_mode=ParseMode.HTML)
    await state.clear()

#Список кампаний
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
    current_campaign = await campaign_repo.get_current(user_id=message.from_user.id)
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