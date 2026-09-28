from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (
    get_or_create_user, get_user, use_generation, 
    activate_subscription, get_stats, get_all_user_ids
)
from keyboards import (
    main_reply_keyboard, stack_selection_keyboard, 
    club_tariffs_keyboard, profile_keyboard, admin_keyboard
)
from engine import generate_specification, STACK_PRESETS
from config import config

# Routers
start_router = Router()
generator_router = Router()
club_router = Router()
profile_router = Router()
admin_router = Router()

# -------------------------------------------------------------
# 1. START & NAVIGATION
# -------------------------------------------------------------
@start_router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    user = message.from_user
    referrer_id = None
    
    if command.args and command.args.startswith("ref_"):
        try:
            ref_candidate = int(command.args.replace("ref_", ""))
            if ref_candidate != user.id:
                referrer_id = ref_candidate
        except ValueError:
            pass
            
    await get_or_create_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name or "Пользователь",
        referrer_id=referrer_id
    )
    
    welcome_text = (
        f"👋 **Привет, {user.first_name}!**\n\n"
        f"Добро пожаловать в **Gromov Scale Hub** — инструмент и комьюнити для тех, "
        f"кто собирает софт и веб-интерфейсы руками ИИ.\n\n"
        f"🎯 **Секрет чистого кода в Cursor & Claude** — не в «магических промптах», "
        f"а в жестком блоке ограничений и правильной архитектуре ТЗ.\n\n"
        f"⚡ **Что здесь есть:**\n"
        f"1. 🛠️ **AI-Генератор ТЗ:** превращает любую сырую мысль в готовое ТЗ с `.cursorrules` "
        f"и блоком `Negative Constraints` (код запускается с 1-й попытки).\n"
        f"2. 💎 **Закрытый Клуб & База:** доступ к библиотеке системных промптов, "
        f"чистым бойлерплейтам и закрытому чату вайбкодеров.\n\n"
        f"🎁 Вам начислено **3 бесплатные генерации ТЗ**!\n\n"
        f"Выберите действие в меню ниже 👇"
    )
    
    await message.answer(
        text=welcome_text,
        reply_markup=main_reply_keyboard(),
        parse_mode="Markdown"
    )

@start_router.message(F.text == "📖 Как пользоваться")
async def msg_how_to(message: Message):
    text = (
        "📖 **Как выжимать максимум из Cursor & Claude:**\n\n"
        "Главная ошибка большинства: просить нейросеть «сделай мне сайт целиком» "
        "или не задавать правила архитектуры. В итоге ИИ генерирует устаревшие библиотеки, "
        "дробит логику на 10 мелких файлов и оставляет `// TODO: fix later`.\n\n"
        "**Рабочий алгоритм:**\n"
        "1. Нажмите «🛠️ Сгенерировать ТЗ для Cursor/Claude».\n"
        "2. Выберите нужный стек (Next.js, Telegram Bot, FastAPI, Mobile).\n"
        "3. Опишите задачу простыми словами (можно даже голосовым сообщением).\n"
        "4. Бот сгенерирует структурированное ТЗ с жестким блоком правил.\n"
        "5. Вставьте полученный промпт в Cursor (`Composer` или `Chat`) — и проект запустится без каши!"
    )
    await message.answer(text=text, parse_mode="Markdown")

@start_router.message(F.text == "🌐 Threads автора")
async def msg_threads(message: Message):
    await message.answer(
        f"🔗 **Официальный Threads Алексея Громова (@gromov.scale):**\n\n"
        f"Там я регулярно разбираю ошибки вайбкодинга, делюсь свежими кейсами сборки софта "
        f"и шаблонами ТЗ для LLM.\n\n"
        f"👉 [Перейти в Threads]({config.THREADS_URL})",
        parse_mode="Markdown",
        disable_web_page_preview=False
    )

# -------------------------------------------------------------
# 2. GENERATOR
# -------------------------------------------------------------
class GenerateTZ(StatesGroup):
    choosing_stack = State()
    waiting_for_idea = State()

@generator_router.message(F.text == "🛠️ Сгенерировать ТЗ для Cursor/Claude")
async def start_tz_generation(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Пожалуйста, сначала отправьте /start")
        return
        
    is_sub = bool(user["is_subscribed"])
    free_left = user["free_generations_left"]
    
    if not is_sub and free_left <= 0:
        await message.answer(
            "⏳ **У вас закончились бесплатные генерации ТЗ.**\n\n"
            "Чтобы продолжить генерировать чистые спецификации без ограничений, "
            "а также получить доступ к закрытой базе System Prompts и чату — оформите подписку на **Gromov Scale Club** 👇",
            reply_markup=club_tariffs_keyboard(),
            parse_mode="Markdown"
        )
        return

    sub_status = "♾️ Безлимит (Подписка активна)" if is_sub else f"🎁 Осталось бесплатных: {free_left}"
    
    await state.set_state(GenerateTZ.choosing_stack)
    await message.answer(
        f"🛠️ **Шаг 1 из 2: Выберите технологический стек**\n\n"
        f"Статус доступа: {sub_status}\n\n"
        f"Под какой стек готовим архитектуру и правила?",
        reply_markup=stack_selection_keyboard(),
        parse_mode="Markdown"
    )

@generator_router.callback_query(F.data.startswith("stack:"))
async def stack_chosen(callback: CallbackQuery, state: FSMContext):
    stack_key = callback.data.split(":")[1]
    await state.update_data(chosen_stack=stack_key)
    await state.set_state(GenerateTZ.waiting_for_idea)
    
    preset_title = STACK_PRESETS.get(stack_key, {}).get("title", stack_key)
    
    await callback.message.edit_text(
        f"Выбран стек: **{preset_title}**\n\n"
        f"📝 **Шаг 2 из 2: Опишите вашу задачу или идею**\n\n"
        f"Напишите простыми словами, что должен делать софт. "
        f"Например:\n"
        f"_«Сервис подписок для Telegram-каналов с личным кабинетом пользователя и интеграцией оплаты через ЮKassa»_\n\n"
        f"Отправьте описание сообщением 👇",
        parse_mode="Markdown"
    )
    await callback.answer()

@generator_router.callback_query(F.data == "cancel")
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Генерация отменена. Вы можете начать заново из главного меню.")
    await callback.answer()

@generator_router.message(GenerateTZ.waiting_for_idea)
async def process_idea(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, отправьте текстовое описание вашей задачи.")
        return
        
    data = await state.get_data()
    stack_key = data.get("chosen_stack", "web_saas")
    
    success = await use_generation(message.from_user.id, stack_key, message.text)
    if not success:
        await message.answer(
            "Лимит генераций исчерпан. Оформите подписку на закрытый клуб для безлимитного доступа 👇",
            reply_markup=club_tariffs_keyboard()
        )
        await state.clear()
        return
        
    await message.answer("⏳ Анализирую архитектуру, формулирую ограничения и собираю ТЗ...")
    
    spec_text = generate_specification(stack_key, message.text)
    await state.clear()
    
    if len(spec_text) <= 4000:
        await message.answer(spec_text, parse_mode="Markdown")
    else:
        doc = BufferedInputFile(spec_text.encode('utf-8'), filename="SPECIFICATION_CURSOR.md")
        await message.answer_document(
            document=doc,
            caption="✅ **Ваше инженерное ТЗ готово!**\nФайл `SPECIFICATION_CURSOR.md` готов к загрузке в корень проекта или вставки в Cursor / Claude."
        )
        
    await message.answer(
        "💡 **Совет по внедрению:**\n"
        "Скопируйте блок `ГОТОВЫЙ СТАРТОВЫЙ ПРОМПТ` и отправьте в Cursor Composer (`Cmd+I` / `Ctrl+I`). "
        "А блок ограничений сохраните в файл `.cursorrules` в корне вашего проекта!",
        parse_mode="Markdown"
    )

# -------------------------------------------------------------
# 3. CLOSED CLUB & PAYWALL
# -------------------------------------------------------------
CLUB_OFFER_TEXT = (
    "💎 **GROMOV SCALE CLUB & ЗАКРЫТАЯ БАЗА ЗНАНИЙ**\n\n"
    "Это закрытое пространство для тех, кто хочет создавать и монетизировать софт "
    "без рутины и бесконечной отладки.\n\n"
    "🔥 **Что вы получаете сразу после входа:**\n"
    "• 📚 **Библиотека System Prompts & `.cursorrules`** под 15+ реальных продакшн-стеков.\n"
    "• 📦 **Чистые Boilerplate-репозитории** (Next.js, Telegram Bots, FastAPI), которые собираются за 1 клик.\n"
    "• 💬 **Закрытый чат практиков вайбкодинга**: разборы кейсов, помощь с багами LLM, обмен клиентами.\n"
    "• ♾️ **Полный безлимит** на генерацию инженерных ТЗ в этом боте.\n\n"
    "💳 **Выберите удобный тариф доступа ниже:**"
)

@club_router.message(F.text == "💎 Закрытый клуб & База")
async def show_club_menu(message: Message):
    await message.answer(
        text=CLUB_OFFER_TEXT,
        reply_markup=club_tariffs_keyboard(),
        parse_mode="Markdown"
    )

@club_router.callback_query(F.data == "go_club")
async def callback_go_club(callback: CallbackQuery):
    await callback.message.answer(
        text=CLUB_OFFER_TEXT,
        reply_markup=club_tariffs_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@club_router.callback_query(F.data == "check_subscription")
async def check_sub_status(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    if user and user["is_subscribed"]:
        until = user["subscription_until"][:10] if user["subscription_until"] else "Бессрочно"
        
        invite_part = ""
        if config.PRIVATE_CHANNEL_ID:
            try:
                invite = await callback.bot.create_chat_invite_link(
                    chat_id=config.PRIVATE_CHANNEL_ID,
                    member_limit=1
                )
                invite_part = f"\n\n👉 [Вступить в закрытый клуб]({invite.invite_link})"
            except Exception:
                invite_part = f"\n\n💬 Напишите @{config.SUPPORT_USERNAME} для добавления в чат."
                
        await callback.message.answer(
            f"🎉 **Ваша подписка активна!**\n"
            f"Срок действия: до **{until}**\n"
            f"Вам доступен полный безлимит генератора ТЗ и закрытая база.{invite_part}",
            parse_mode="Markdown"
        )
    else:
        await callback.message.answer(
            "🔎 **Оплата пока не обнаружена.**\n\n"
            "Если вы только что оплатили через платёжную систему, подождите 1–2 минуты "
            "для синхронизации и нажмите проверку ещё раз.\n\n"
            f"Если возникли вопросы — напишите напрямую автору: @{config.SUPPORT_USERNAME}",
            parse_mode="Markdown"
        )
    await callback.answer()

# -------------------------------------------------------------
# 4. PROFILE & REFERRAL
# -------------------------------------------------------------
@profile_router.message(F.text == "👤 Мой профиль")
async def show_profile(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Пожалуйста, сначала отправьте /start")
        return
        
    is_sub = bool(user["is_subscribed"])
    sub_text = "🟢 **Активна (Безлимит)**" if is_sub else "⚪️ **Не активна (Базовый тариф)**"
    
    if is_sub and user["subscription_until"]:
        sub_text += f"\nДействует до: `{user['subscription_until'][:10]}`"
        
    gens_left = "♾️ Безлимитно" if is_sub else f"{user['free_generations_left']} шт."
    bot_info = await message.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{message.from_user.id}"
    
    profile_text = (
        f"👤 **ЛИЧНЫЙ КАБИНЕТ**\n\n"
        f"🆔 Ваш ID: `{user['user_id']}`\n"
        f"💎 Статус подписки: {sub_text}\n"
        f"⚡ Доступных генераций ТЗ: **{gens_left}**\n"
        f"📊 Всего сгенерировано ТЗ: **{user['generations_count']}**\n\n"
        f"🎁 **Реферальная программа:**\n"
        f"Приглашайте друзей и коллег-вайбкодеров! За каждого приглашенного вы оба получаете "
        f"по **+3 бесплатные генерации** ТЗ.\n\n"
        f"Ваша реферальная ссылка:\n`{ref_link}`"
    )
    
    await message.answer(
        text=profile_text,
        reply_markup=profile_keyboard(ref_link),
        parse_mode="Markdown"
    )

# -------------------------------------------------------------
# 5. ADMIN PANEL
# -------------------------------------------------------------
def is_admin(user_id: int) -> bool:
    return config.ADMIN_ID != 0 and user_id == config.ADMIN_ID

@admin_router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        if config.ADMIN_ID == 0:
            config.ADMIN_ID = message.from_user.id
        else:
            return
            
    stats = await get_stats()
    text = (
        f"👑 **ПАНЕЛЬ АДМИНИСТРАТОРА**\n\n"
        f"👥 Всего пользователей: **{stats['total_users']}**\n"
        f"💎 Активных подписок: **{stats['active_subs']}**\n"
        f"⚡ Всего сгенерировано ТЗ: **{stats['total_gens']}**\n\n"
        f"**Команды:**\n"
        f"• `/give_sub <user_id> <дней>` — выдать подписку пользователю вручную\n"
        f"• `/broadcast <текст>` — сделать рассылку по всем пользователям"
    )
    await message.answer(text=text, reply_markup=admin_keyboard(), parse_mode="Markdown")

@admin_router.callback_query(F.data == "admin_stats")
async def cb_admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    stats = await get_stats()
    text = (
        f"📊 **Свежая статистика:**\n\n"
        f"• Пользователей в базе: {stats['total_users']}\n"
        f"• Платных подписок: {stats['active_subs']}\n"
        f"• Сгенерировано ТЗ: {stats['total_gens']}"
    )
    await callback.message.edit_text(text=text, reply_markup=admin_keyboard(), parse_mode="Markdown")
    await callback.answer()

@admin_router.message(Command("give_sub"))
async def cmd_give_sub(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Формат: `/give_sub <user_id> <дней>`", parse_mode="Markdown")
        return
    try:
        target_id = int(parts[1])
        days = int(parts[2])
        await activate_subscription(target_id, days)
        await message.answer(f"✅ Подписка на {days} дней успешно выдана пользователю `{target_id}`!")
        try:
            await message.bot.send_message(
                chat_id=target_id,
                text=f"🎉 **Вам активирована подписка на Gromov Scale Club на {days} дней!**\nТеперь вам доступен полный безлимит генератора ТЗ и закрытая база.",
                parse_mode="Markdown"
            )
        except Exception:
            pass
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@admin_router.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    if not is_admin(message.from_user.id):
        return
    text_to_send = message.text.replace("/broadcast", "").strip()
    if not text_to_send:
        await message.answer("Формат: `/broadcast <текст рассылки>`", parse_mode="Markdown")
        return
        
    user_ids = await get_all_user_ids()
    sent = 0
    await message.answer(f"🚀 Запускаю рассылку по {len(user_ids)} пользователям...")
    
    for uid in user_ids:
        try:
            await message.bot.send_message(chat_id=uid, text=text_to_send, parse_mode="Markdown")
            sent += 1
        except Exception:
            pass
            
    await message.answer(f"✅ Рассылка завершена. Успешно доставлено: {sent}/{len(user_ids)}")
