import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from config import config
from database import init_db
from handlers import start, generator, club, profile, admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="🚀 Главное меню"),
        BotCommand(command="profile", description="👤 Личный кабинет и рефералка"),
        BotCommand(command="club", description="💎 Закрытый клуб & База"),
        BotCommand(command="admin", description="👑 Админ-панель")
    ]
    await bot.set_my_commands(commands)

import os
from aiohttp import web

async def health_check(request):
    return web.Response(text="OK - Gromov Scale Bot is running!")

async def start_web_server():
    port = int(os.getenv("PORT", 8080))
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health check HTTP server running on port {port}")

async def main():
    logger.info("Initializing database...")
    await init_db()
    
    # Start health check server for Render.com free tier
    try:
        await start_web_server()
    except Exception as e:
        logger.warning(f"Could not start health check server (non-critical): {e}")
    
    session = None
    if config.PROXY_URL:
        logger.info(f"Using proxy: {config.PROXY_URL}")
        session = AiohttpSession(proxy=config.PROXY_URL)
        
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
        session=session
    )
    
    dp = Dispatcher()
    
    # Register routers in priority order
    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(generator.router)
    dp.include_router(club.router)
    dp.include_router(profile.router)
    
    while True:
        try:
            bot_info = await bot.get_me()
            logger.info(f"Bot started successfully as @{bot_info.username} ({bot_info.first_name})")
            await set_bot_commands(bot)
            
            # Drop pending updates to prevent backlog processing
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(bot)
            break
        except Exception as e:
            logger.error(f"Error during bot execution: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)
    
    await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
