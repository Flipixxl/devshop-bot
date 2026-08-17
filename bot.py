import asyncio
import logging
from pathlib import Path

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import MenuButtonWebApp, WebAppInfo

from config import load_config
from database import init_db
from handlers import router
from seed import seed_data
from web_server import configure as configure_server, create_app

LOG_FILE = Path(__file__).resolve().parent / "bot.log"


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.getLogger().addHandler(file_handler)


async def main() -> None:
    setup_logging()

    config = load_config()
    if not config.bot_token:
        raise SystemExit("BOT_TOKEN не задан. Скопируйте .env.example в .env и заполните его.")
    if not config.webapp_url:
        raise SystemExit(
            "WEBAPP_URL не задан. Запустите cloudflared tunnel --url http://localhost:8080 "
            "и впишите полученную HTTPS-ссылку в .env."
        )

    await init_db()
    await seed_data()

    bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp["config"] = config
    dp.include_router(router)

    app = create_app()
    configure_server(bot, config)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, config.host, config.port)
    await site.start()
    logging.info("Mini App server started on http://%s:%s", config.host, config.port)

    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(text="🛍 Магазин", web_app=WebAppInfo(url=config.webapp_url))
    )

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())