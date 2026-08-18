from database import _connect, init_db

CATALOG = [
    (
        "Техника",
        "🖥",
        [
            {
                "name": "Ноутбук DevPro 14",
                "description": "Производительный ноутбук для разработчиков: AMD Ryzen 7, 16 ГБ ОЗУ, SSD 512 ГБ.",
                "price": 84990,
                "photo_url": "/static/img/products/product-1.jpg",
                "emoji": "💻",
                "stock": 12,
            },
            {
                "name": "Моноблок Studio 27",
                "description": "Моноблок с 4K-экраном 27″ для дизайнеров и верстальщиков.",
                "price": 124990,
                "photo_url": "/static/img/products/product-2.jpg",
                "emoji": "🖥️",
                "stock": 4,
            },
            {
                "name": "Мини-ПК CodeBox i7",
                "description": "Компактный системный блок: Core i7, 32 ГБ ОЗУ, NVMe 1 ТБ. Поместится даже в рюкзак.",
                "price": 56990,
                "photo_url": "/static/img/products/product-3.jpg",
                "emoji": "🖲️",
                "stock": 8,
            },
            {
                "name": "Монитор PixelView 27",
                "description": "27″ QHD IPS, 144 Гц, 100% sRGB — отличный выбор для кода и контента.",
                "price": 32990,
                "photo_url": "/static/img/products/product-4.jpg",
                "emoji": "📺",
                "stock": 15,
            },
        ],
    ),
    (
        "Аксессуары",
        "⌨️",
        [
            {
                "name": "Клавиатура KeyCraft TKL",
                "description": "Механическая клавиатура без цифрового блока: hot-swap, подсветка RGB, тактильный отклик.",
                "price": 9990,
                "photo_url": "/static/img/products/product-5.jpg",
                "emoji": "⌨️",
                "stock": 25,
            },
            {
                "name": "Мышь SwiftPro",
                "description": "Лёгкая мышь 69 г с сенсором 26 000 DPI для работы и игр.",
                "price": 4490,
                "photo_url": "/static/img/products/product-6.jpg",
                "emoji": "🖱️",
                "stock": 40,
            },
            {
                "name": "Наушники AirPulse",
                "description": "Беспроводные накладные наушники с активным шумоподавлением.",
                "price": 7990,
                "photo_url": "/static/img/products/product-7.jpg",
                "emoji": "🎧",
                "stock": 18,
            },
            {
                "name": "Коврик DeskMat XL",
                "description": "Плотный коврик 900×400 мм с прошитыми краями.",
                "price": 1290,
                "photo_url": "/static/img/products/product-8.jpg",
                "emoji": "🎮",
                "stock": 60,
            },
        ],
    ),
    (
        "Софт и лицензии",
        "💾",
        [
            {
                "name": "Windows 11 Pro (лицензия)",
                "description": "Лицензионный ключ Windows 11 Pro. Ключ приходит в сообщении после оплаты.",
                "price": 2990,
                "photo_url": "/static/img/products/product-9.png",
                "emoji": "🪟",
                "stock": 100,
            },
            {
                "name": "Office 2024 (лицензия)",
                "description": "Классический пакет Office: Word, Excel, PowerPoint на русском языке.",
                "price": 4590,
                "photo_url": "/static/img/products/product-10.png",
                "emoji": "📄",
                "stock": 50,
            },
            {
                "name": "Облако 1 ТБ на 1 год",
                "description": "Облачное хранилище на 1 ТБ для бэкапов и рабочих файлов.",
                "price": 1990,
                "photo_url": "/static/img/products/product-11.jpg",
                "emoji": "☁️",
                "stock": 200,
            },
            {
                "name": "Настройка ПК под ключ",
                "description": "Услуга: установка Windows, драйверов и софта под ключ. Удалённо.",
                "price": 2490,
                "photo_url": "/static/img/products/product-12.jpg",
                "emoji": "🔧",
                "stock": 10,
            },
        ],
    ),
]

# Синхронизация картинок и эмодзи с каталогом в уже существующих БД.
IMAGE_MAP = {
    prod["name"]: (prod["emoji"], prod["photo_url"])
    for _, _, products in CATALOG
    for prod in products
}


async def seed_data() -> None:
    await init_db()
    conn = await _connect()
    try:
        rows = await conn.execute_fetchall("SELECT COUNT(*) AS count FROM products")
        if rows[0]["count"] > 0:
            # Старые БД: перезаписываем photo_url/emoji по имени товара (идемпотентно).
            for name, (emoji, photo_url) in IMAGE_MAP.items():
                await conn.execute(
                    "UPDATE products SET photo_url = ?, emoji = ? WHERE name = ?",
                    (photo_url, emoji, name),
                )
            await conn.commit()
            return
        for category_name, emoji, products in CATALOG:
            cur = await conn.execute(
                "INSERT INTO categories (name, emoji) VALUES (?, ?)", (category_name, emoji)
            )
            category_id = cur.lastrowid
            await conn.executemany(
                "INSERT INTO products (category_id, name, description, price, photo_url, emoji, stock) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        category_id,
                        prod["name"],
                        prod["description"],
                        prod["price"],
                        prod["photo_url"],
                        prod["emoji"],
                        prod["stock"],
                    )
                    for prod in products
                ],
            )
        await conn.commit()
    finally:
        await conn.close()