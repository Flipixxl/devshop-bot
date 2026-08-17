import os
from pathlib import Path

import aiosqlite

DATA_DIR = Path(os.getenv("DATA_DIR") or (Path(__file__).resolve().parent))
DB_PATH = DATA_DIR / "shop.db"

ORDER_STATUSES = {
    "new": "🆕 Новый",
    "processing": "🔄 В обработке",
    "done": "✅ Выполнен",
    "cancelled": "❌ Отменён",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    emoji TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    price INTEGER NOT NULL,
    photo_url TEXT NOT NULL DEFAULT '',
    stock INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS cart_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 1,
    UNIQUE (user_id, product_id)
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    customer_name TEXT NOT NULL,
    phone TEXT NOT NULL DEFAULT '',
    total INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'new',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL,
    product_name TEXT NOT NULL,
    price INTEGER NOT NULL,
    quantity INTEGER NOT NULL
);
"""


async def _connect() -> aiosqlite.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys = ON")
    return conn


async def init_db() -> None:
    conn = await _connect()
    try:
        await conn.executescript(SCHEMA)
        await conn.commit()
    finally:
        await conn.close()


async def get_categories() -> list[dict]:
    conn = await _connect()
    try:
        rows = await conn.execute_fetchall("SELECT * FROM categories ORDER BY id")
        return [dict(row) for row in rows]
    finally:
        await conn.close()


async def get_products_by_category(category_id: int) -> list[dict]:
    conn = await _connect()
    try:
        rows = await conn.execute_fetchall(
            "SELECT * FROM products WHERE category_id = ? ORDER BY id", (category_id,)
        )
        return [dict(row) for row in rows]
    finally:
        await conn.close()


async def get_product(product_id: int) -> dict | None:
    conn = await _connect()
    try:
        rows = await conn.execute_fetchall("SELECT * FROM products WHERE id = ?", (product_id,))
        return dict(rows[0]) if rows else None
    finally:
        await conn.close()


async def get_cart_items(user_id: int) -> list[dict]:
    conn = await _connect()
    try:
        rows = await conn.execute_fetchall(
            """SELECT c.product_id, p.name, p.price, c.quantity
               FROM cart_items c
               JOIN products p ON p.id = c.product_id
               WHERE c.user_id = ?
               ORDER BY p.id""",
            (user_id,),
        )
        return [dict(row) for row in rows]
    finally:
        await conn.close()


async def cart_total(user_id: int) -> int:
    conn = await _connect()
    try:
        rows = await conn.execute_fetchall(
            """SELECT SUM(p.price * c.quantity) AS total
               FROM cart_items c
               JOIN products p ON p.id = c.product_id
               WHERE c.user_id = ?""",
            (user_id,),
        )
        return rows[0]["total"] or 0 if rows else 0
    finally:
        await conn.close()


async def add_to_cart(user_id: int, product_id: int) -> None:
    conn = await _connect()
    try:
        await conn.execute(
            """INSERT INTO cart_items (user_id, product_id, quantity)
               VALUES (?, ?, 1)
               ON CONFLICT (user_id, product_id)
               DO UPDATE SET quantity = MIN(quantity + 1, 99)""",
            (user_id, product_id),
        )
        await conn.commit()
    finally:
        await conn.close()


async def set_quantity(user_id: int, product_id: int, quantity: int) -> None:
    conn = await _connect()
    try:
        if quantity <= 0:
            await conn.execute(
                "DELETE FROM cart_items WHERE user_id = ? AND product_id = ?",
                (user_id, product_id),
            )
        else:
            await conn.execute(
                """INSERT INTO cart_items (user_id, product_id, quantity)
                   VALUES (?, ?, ?)
                   ON CONFLICT (user_id, product_id)
                   DO UPDATE SET quantity = excluded.quantity""",
                (user_id, product_id, min(quantity, 99)),
            )
        await conn.commit()
    finally:
        await conn.close()


async def get_catalog() -> list[dict]:
    conn = await _connect()
    try:
        categories = await conn.execute_fetchall("SELECT * FROM categories ORDER BY id")
        result = []
        for category in categories:
            products = await conn.execute_fetchall(
                "SELECT * FROM products WHERE category_id = ? ORDER BY id",
                (category["id"],),
            )
            item = dict(category)
            item["products"] = [dict(product) for product in products]
            result.append(item)
        return result
    finally:
        await conn.close()


async def change_quantity(user_id: int, product_id: int, delta: int) -> None:
    conn = await _connect()
    try:
        await conn.execute(
            """UPDATE cart_items
               SET quantity = MAX(0, MIN(quantity + ?, 99))
               WHERE user_id = ? AND product_id = ?""",
            (delta, user_id, product_id),
        )
        await conn.execute(
            "DELETE FROM cart_items WHERE user_id = ? AND product_id = ? AND quantity <= 0",
            (user_id, product_id),
        )
        await conn.commit()
    finally:
        await conn.close()


async def remove_from_cart(user_id: int, product_id: int) -> None:
    conn = await _connect()
    try:
        await conn.execute(
            "DELETE FROM cart_items WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        )
        await conn.commit()
    finally:
        await conn.close()


async def clear_cart(user_id: int) -> None:
    conn = await _connect()
    try:
        await conn.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))
        await conn.commit()
    finally:
        await conn.close()


async def create_order(user_id: int, customer_name: str, phone: str) -> int | None:
    conn = await _connect()
    try:
        rows = await conn.execute_fetchall(
            """SELECT p.id AS product_id, p.name, p.price, c.quantity
               FROM cart_items c
               JOIN products p ON p.id = c.product_id
               WHERE c.user_id = ?
               ORDER BY p.id""",
            (user_id,),
        )
        if not rows:
            return None
        total = sum(row["price"] * row["quantity"] for row in rows)
        cur = await conn.execute(
            "INSERT INTO orders (user_id, customer_name, phone, total) VALUES (?, ?, ?, ?)",
            (user_id, customer_name, phone, total),
        )
        order_id = cur.lastrowid
        await conn.executemany(
            "INSERT INTO order_items (order_id, product_id, product_name, price, quantity) VALUES (?, ?, ?, ?, ?)",
            [
                (order_id, row["product_id"], row["name"], row["price"], row["quantity"])
                for row in rows
            ],
        )
        await conn.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))
        await conn.commit()
        return order_id
    finally:
        await conn.close()


async def get_orders(
    user_id: int | None = None, status: str | None = None, limit: int = 10
) -> list[dict]:
    conn = await _connect()
    try:
        query = "SELECT * FROM orders"
        conditions = []
        params: list = []
        if user_id is not None:
            conditions.append("user_id = ?")
            params.append(user_id)
        if status is not None:
            conditions.append("status = ?")
            params.append(status)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        rows = await conn.execute_fetchall(query, params)
        return [dict(row) for row in rows]
    finally:
        await conn.close()


async def get_order(order_id: int) -> dict | None:
    conn = await _connect()
    try:
        rows = await conn.execute_fetchall("SELECT * FROM orders WHERE id = ?", (order_id,))
        return dict(rows[0]) if rows else None
    finally:
        await conn.close()


async def get_order_items(order_id: int) -> list[dict]:
    conn = await _connect()
    try:
        rows = await conn.execute_fetchall(
            "SELECT * FROM order_items WHERE order_id = ? ORDER BY id", (order_id,)
        )
        return [dict(row) for row in rows]
    finally:
        await conn.close()


async def set_order_status(order_id: int, status: str) -> None:
    conn = await _connect()
    try:
        await conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        await conn.commit()
    finally:
        await conn.close()
