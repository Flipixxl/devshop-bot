# DevShop — Telegram Mini App интернет-магазин

Портфолио-проект: бот-магазин на **Aiogram 3** + **aiohttp** с интерфейсом в **Telegram Mini App**.

## Возможности

- Каталог: категории → товары → карточка (фото, описание, цена, наличие)
- Корзина: изменение количества, удаление, очистка
- Оформление заказа: имя + телефон → заказ в БД (SQLite)
- Уведомление админу в Telegram о новом заказе
- Админ-панель внутри мини-аппа: заказы, фильтры по статусу, смена статуса, уведомления клиенту
- Безопасность: каждый запрос к API проходит валидацию `initData` Telegram (HMAC-подпись)

## Стек

- Aiogram 3 (бот, поллинг)
- aiohttp (веб-сервер мини-аппа: статика + REST API)
- aiosqlite (SQLite)
- Vanilla HTML/CSS/JS (без сборки)

## Структура

```
bot.py          — точка входа: aiohttp-сервер + поллинг бота
handlers.py     — /start и кнопка мини-аппа
web_server.py   — REST API + статика
auth.py         — валидация initData
database.py     — SQLite-слой
seed.py         — автонаполнение каталога
web/            — фронтенд мини-аппа (index.html, style.css, app.js)
```

## Запуск локально

1. Создай бота в @BotFather, получи токен и ID админа (узнать свой ID — у @userinfobot).
2. `cp .env.example .env` и заполни `BOT_TOKEN`, `ADMIN_IDS`, `WEBAPP_URL` (HTTPS-ссылка на мини-апп).
3. Установи зависимости: `pip install -r requirements.txt`
4. Подними HTTPS-туннель к `http://localhost:8080` (например `serveo.net`), впиши URL в `.env`.
5. Запусти: `python bot.py`
6. В @BotFather → `/setdomain` добавь домен туннеля.

## Деплой на Railway

1. Залей этот проект на GitHub.
2. В Railway: **New Project → Deploy from GitHub repo** — Dockerfile определится автоматически.
3. Env vars: `BOT_TOKEN`, `ADMIN_IDS`, `WEBAPP_URL` (домен Railway, вида `https://xxx.up.railway.app`).
4. **Volumes**: добавь Persistent Volume с путём монтирования `/data` — там живёт `shop.db`.
5. Открой мини-апп по домену Railway и добавь этот домен в @BotFather → `/setdomain`.

## Фото товаров

Изображения товаров взяты с [Wikimedia Commons](https://commons.wikimedia.org) (свободные лицензии, размер миниатюр 1280px) и хранятся локально в `web/static/img/products/`:

- product-1: [Schenker VIA14 Laptop asv2021-01](https://commons.wikimedia.org/wiki/File:Schenker_VIA14_Laptop_asv2021-01.jpg)
- product-2: [IMac Pro (2017)](https://commons.wikimedia.org/wiki/File:IMac_Pro_(2017).jpg)
- product-3: [Antec ISK110 mini-PC front-left](https://commons.wikimedia.org/wiki/File:Antec_ISK110_mini-PC_front-left.JPG)
- product-4: [Computer monitor screen image simulated](https://commons.wikimedia.org/wiki/File:Computer_monitor_screen_image_simulated.jpg)
- product-5: [Beautiful Mechanical Keyboard](https://commons.wikimedia.org/wiki/File:Beautiful_Mechanical_Keyboard.jpg)
- product-6: [Logitech G903 Lightspeed](https://commons.wikimedia.org/wiki/File:2023_Mysz_komputerowa_Logitech_G903_Lightspeed.jpg)
- product-7: [Bose QuietComfort 25](https://commons.wikimedia.org/wiki/File:Bose_QuietComfort_25_Acoustic_Noise_Cancelling_Headphones_with_Carry_Case.jpg)
- product-8: [Razer Destructor 2 (top)](https://commons.wikimedia.org/wiki/File:Razer_Destructor_2-top_PNr%C2%B00406.jpg)
- product-9: [Windows 11 desktop](https://commons.wikimedia.org/wiki/File:Windows_11_22000.71_x64-2021-07-19-11-42-12_ohne_Cursor.png)
- product-10: [Microsoft Office logo (2013–2019)](https://commons.wikimedia.org/wiki/File:Microsoft_Office_logo_(2013%E2%80%932019).svg)
- product-11: [Quanta Computer cloud servers](https://commons.wikimedia.org/wiki/File:Quanta_Computer_cloud_computing_servers_at_COSCUP_20120819.jpg)
- product-12: [Computer repair in progress](https://commons.wikimedia.org/wiki/File:Computer_repair_in_progress.jpg)