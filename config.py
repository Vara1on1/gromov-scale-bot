import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "8814312826:AAFIMWSQ-fXhLh0fthzW3chPoV1XL-kfhD4")
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))
    
    # Платёжные ссылки (Tribute / Paywall / Кастомная ссылка)
    PAYMENT_URL_MONTH: str = os.getenv("PAYMENT_URL_MONTH", "https://t.me/tribute")
    PAYMENT_URL_QUARTER: str = os.getenv("PAYMENT_URL_QUARTER", "https://t.me/tribute")
    
    # Ссылка на закрытый канал клуба или бота техподдержки
    PRIVATE_CHANNEL_ID: str = os.getenv("PRIVATE_CHANNEL_ID", "")
    SUPPORT_USERNAME: str = os.getenv("SUPPORT_USERNAME", "gromov_scale")
    THREADS_URL: str = "https://www.threads.com/@gromov.scale"
    
    # Лимиты
    FREE_GENERATIONS_LIMIT: int = 3
    REFERRAL_BONUS_GENERATIONS: int = 3
    
    # Прокси (если запуск локально в РФ без VPN: например socks5://127.0.0.1:1080 или http://...)
    PROXY_URL: str = os.getenv("PROXY_URL", "")

config = Config()
