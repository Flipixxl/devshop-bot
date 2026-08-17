from pathlib import Path

from aiohttp import web

from auth import get_user_id_from_init_data, parse_init_data
from config import Config
from database import (
    ORDER_STATUSES,
    clear_cart,
    create_order,
    get_cart_items,
    get_catalog,
    get_order,
    get_order_items,
    get_orders,
    get_product,
    set_order_status,
    set_quantity,
)
from utils import admin_notify_text

WEB_DIR = Path(__file__).resolve().parent / "web"
INDEX_FILE = WEB_DIR / "index.html"

_bot = None
_cfg: Config = None


def configure(bot, config: Config) -> None:
    global _bot, _cfg
    _bot = bot
    _cfg = config


def _json(data, status: int = 200) -> web.Response:
    return web.json_response(data, status=status)


def _error(message: str, status: int = 400) -> web.Response:
    return _json({"ok": False, "error": message}, status=status)


def _is_admin(user_id: int) -> bool:
    return _cfg is not None and user_id in _cfg.admin_ids


def _require_user(func):
    async def wrapper(request):
        init_data = request.headers.get("X-Init-Data", "")
        user_id = get_user_id_from_init_data(_cfg.bot_token, init_data)
        if user_id is None:
            return _json({"ok": False, "error": "unauthorized"}, status=401)
        request["user_id"] = user_id
        return await func(request)

    return wrapper


def _require_admin(func):
    async def wrapper(request):
        init_data = request.headers.get("X-Init-Data", "")
        user_id = get_user_id_from_init_data(_cfg.bot_token, init_data)
        if user_id is None:
            return _json({"ok": False, "error": "unauthorized"}, status=401)
        if not _is_admin(user_id):
            return _json({"ok": False, "error": "forbidden"}, status=403)
        request["user_id"] = user_id
        return await func(request)

    return wrapper


async def _notify_admins(order: dict, items: list[dict]) -> None:
    if _bot is None or _cfg is None:
        return
    text = admin_notify_text(order, items)
    for admin_id in _cfg.admin_ids:
        try:
            await _bot.send_message(admin_id, text)
        except Exception:
            continue


async def _cart_payload(user_id: int) -> dict:
    items = await get_cart_items(user_id)
    return {
        "ok": True,
        "items": items,
        "total": sum(item["price"] * item["quantity"] for item in items),
        "count": sum(item["quantity"] for item in items),
    }


async def index(request: web.Request) -> web.FileResponse:
    return web.FileResponse(INDEX_FILE)


async def api_me(request: web.Request) -> web.Response:
    user_id = request["user_id"]
    data = parse_init_data(_cfg.bot_token, request.headers.get("X-Init-Data", ""))
    first_name = data.user.first_name if data and data.user else ""
    return _json(
        {
            "ok": True,
            "user_id": user_id,
            "is_admin": _is_admin(user_id),
            "first_name": first_name,
        }
    )


async def api_catalog(request: web.Request) -> web.Response:
    return _json({"ok": True, "categories": await get_catalog()})


async def api_product(request: web.Request) -> web.Response:
    product = await get_product(int(request.match_info["product_id"]))
    if product is None:
        return _error("Товар не найден", 404)
    return _json({"ok": True, "product": product})


async def api_cart(request: web.Request) -> web.Response:
    return _json(await _cart_payload(request["user_id"]))


async def api_cart_set(request: web.Request) -> web.Response:
    body = await request.json()
    product_id = int(body.get("product_id", 0))
    quantity = int(body.get("quantity", 0))
    product = await get_product(product_id)
    if product is None:
        return _error("Товар не найден", 404)
    await set_quantity(request["user_id"], product_id, quantity)
    return _json(await _cart_payload(request["user_id"]))


async def api_cart_clear(request: web.Request) -> web.Response:
    await clear_cart(request["user_id"])
    return _json(await _cart_payload(request["user_id"]))


async def api_orders_create(request: web.Request) -> web.Response:
    body = await request.json()
    name = (body.get("name") or "").strip()
    phone = (body.get("phone") or "").strip()
    if not name or len(name) > 60:
        return _error("Введите корректное имя")
    if not phone:
        return _error("Введите номер телефона")
    user_id = request["user_id"]
    order_id = await create_order(user_id, name, phone)
    if order_id is None:
        return _error("Корзина пуста")
    order = await get_order(order_id)
    items = await get_order_items(order_id)
    await _notify_admins(order, items)
    return _json({"ok": True, "order": order, "items": items})


async def api_my_orders(request: web.Request) -> web.Response:
    orders = await get_orders(user_id=request["user_id"], limit=20)
    return _json({"ok": True, "orders": orders})


async def api_admin_orders(request: web.Request) -> web.Response:
    status = request.query.get("status") or None
    orders = await get_orders(status=status, limit=20)
    return _json({"ok": True, "orders": orders})


async def api_admin_order(request: web.Request) -> web.Response:
    order = await get_order(int(request.match_info["order_id"]))
    if order is None:
        return _error("Заказ не найден", 404)
    items = await get_order_items(order["id"])
    return _json({"ok": True, "order": order, "items": items})


async def api_admin_order_patch(request: web.Request) -> web.Response:
    order = await get_order(int(request.match_info["order_id"]))
    if order is None:
        return _error("Заказ не найден", 404)
    body = await request.json()
    status = body.get("status", "")
    if status not in ORDER_STATUSES:
        return _error("Неизвестный статус")
    await set_order_status(order["id"], status)
    updated = await get_order(order["id"])
    return _json({"ok": True, "order": updated})


async def api_admin_order_notify(request: web.Request) -> web.Response:
    order = await get_order(int(request.match_info["order_id"]))
    if order is None:
        return _error("Заказ не найден", 404)
    body = await request.json()
    mode = body.get("mode", "status")
    if mode == "status":
        text = (
            f"📦 <b>Статус заказа #{order['id']}</b>: {ORDER_STATUSES[order['status']]}\n\n"
            "Спасибо, что выбрали наш магазин!"
        )
    elif mode == "text":
        text = (body.get("text") or "").strip()
        if not text:
            return _error("Введите текст сообщения")
        text = f"📩 <b>Сообщение от магазина</b>\n\n{text}"
    else:
        return _error("Неизвестный режим отправки")
    try:
        await _bot.send_message(order["user_id"], text)
    except Exception:
        return _error("Не удалось отправить: клиент не начал диалог с ботом", 400)
    return _json({"ok": True, "message": "Сообщение отправлено клиенту"})


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_get("/index.html", index)
    app.router.add_static("/static/", WEB_DIR / "static")

    app.router.add_get("/api/me", _require_user(api_me))
    app.router.add_get("/api/catalog", _require_user(api_catalog))
    app.router.add_get("/api/products/{product_id}", _require_user(api_product))
    app.router.add_get("/api/cart", _require_user(api_cart))
    app.router.add_post("/api/cart/set", _require_user(api_cart_set))
    app.router.add_post("/api/cart/clear", _require_user(api_cart_clear))
    app.router.add_post("/api/orders", _require_user(api_orders_create))
    app.router.add_get("/api/orders", _require_user(api_my_orders))

    app.router.add_get("/api/admin/orders", _require_admin(api_admin_orders))
    app.router.add_get("/api/admin/orders/{order_id}", _require_admin(api_admin_order))
    app.router.add_patch("/api/admin/orders/{order_id}", _require_admin(api_admin_order_patch))
    app.router.add_post(
        "/api/admin/orders/{order_id}/notify", _require_admin(api_admin_order_notify)
    )
    return app