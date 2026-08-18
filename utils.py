from html import escape


def fmt_price(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def admin_notify_text(order: dict, items: list[dict]) -> str:
    lines = ["🛒 <b>Новый заказ!</b>", f"Номер: #{order['id']}", "", "📦 Состав:"]
    lines += [
        f"• {escape(item['product_name'])} × {item['quantity']} — "
        f"{fmt_price(item['price'] * item['quantity'])} ₽"
        for item in items
    ]
    lines += [
        "",
        f"Итого: <b>{fmt_price(order['total'])} ₽</b>",
        "",
        f"👤 Клиент: {escape(order['customer_name'])}",
        f"📱 Телефон: {escape(order['phone'])}",
    ]
    return "\n".join(lines)