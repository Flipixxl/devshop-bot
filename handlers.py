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
                    text="Открыть магазин",
                    web_app=WebAppInfo(url=config.webapp_url),
                )
            ]
        ]
    )
    user = message.from_user
    name = user.first_name if user else ""
    greeting = f", {name}" if name else ""
    await message.answer(
        f"Привет{greeting}!\n\n"
        "<b>DevShop</b> — магазин техники, аксессуаров и лицензий. "
        "Всё оформляется прямо здесь, в Telegram.\n\n"
        "Что в каталоге:\n"
        "• Техника — ноутбуки, моноблоки, мониторы\n"
        "• Аксессуары — клавиатуры, мыши, наушники\n"
        "• Лицензии — Windows, Office, облако\n\n"
        "Как сделать заказ:\n"
        "1. Нажмите «Открыть магазин»\n"
        "2. Соберите корзину и оформите заказ\n"
        "3. Следите за статусом в разделе «Мои заказы»\n\n"
        "Менеджер на связи — отвечаем быстро.",
        reply_markup=keyboard,
    )