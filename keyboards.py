from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from config import config

def main_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛠️ Сгенерировать ТЗ для Cursor/Claude")],
            [KeyboardButton(text="💎 Закрытый клуб & База"), KeyboardButton(text="👤 Мой профиль")],
            [KeyboardButton(text="📖 Как пользоваться"), KeyboardButton(text="🌐 Threads автора")]
        ],
        resize_keyboard=True
    )

def stack_selection_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Web App / SaaS (Next.js, Tailwind)", callback_data="stack:web_saas")],
            [InlineKeyboardButton(text="🤖 Telegram Bot (Python, Aiogram 3)", callback_data="stack:tg_bot")],
            [InlineKeyboardButton(text="⚡ Backend API (FastAPI, Docker)", callback_data="stack:fastapi_backend")],
            [InlineKeyboardButton(text="📱 Mobile App (React Native, Expo)", callback_data="stack:mobile_expo")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
        ]
    )

def club_tariffs_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⭐️ 1 месяц — 790 ₽", url=config.PAYMENT_URL_MONTH)],
            [InlineKeyboardButton(text="🔥 3 месяца — 1 990 ₽ (Скидка 20%)", url=config.PAYMENT_URL_QUARTER)],
            [InlineKeyboardButton(text="✅ Я оплатил / Проверить подписку", callback_data="check_subscription")],
            [InlineKeyboardButton(text="💬 Написать автору / Задать вопрос", url=f"https://t.me/{config.SUPPORT_USERNAME}")]
        ]
    )

def profile_keyboard(ref_link: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💎 Оформить / Продлить подписку", callback_data="go_club")],
            [InlineKeyboardButton(text="🔗 Поделиться ссылкой (+3 генерации)", switch_inline_query=f"\nПопробуй генератор чистых ТЗ для Cursor: {ref_link}")]
        ]
    )

def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")]
        ]
    )
