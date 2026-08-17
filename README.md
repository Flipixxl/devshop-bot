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