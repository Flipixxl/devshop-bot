from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from config import Config

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, config: Config) -> None:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛍 Открыть магазин",
                    web_app=WebAppInfo(url=config.webapp_url),
                )
            ]
        ]
    )
    await message.answer(
        "👋 <b>Добро пожаловать в IT-магазин DevShop!</b>\n\n"
        "Весь магазин живёт в мини-приложении: каталог, корзина, "
        "оформление заказа и админ-панель.\n\n"
        "Нажмите кнопку ниже, чтобы открыть его 👇",
        reply_markup=keyboard,
    )