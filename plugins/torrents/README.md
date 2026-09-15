# Торренты (Torrents Plugin)

Плагин для управления загрузками торрентов, интеграции с трекерами и медиа-библиотеками.

## Назначение
Обеспечивает поиск релизов в TMDb, интеграцию с индексерами через Prowlarr и передачу загрузок в клиент qBittorrent.

## Настройки (Через панель администрирования Home.Media)
В манифесте `manifest.json` плагина определены следующие настройки, которые необходимо заполнить в интерфейсе Ядра:
- **TMDb API Key** (`tmdb_api_key`) — Ключ API для поиска фильмов и сериалов.
- **Prowlarr URL** (`prowlarr_url`) — Адрес установленного Prowlarr.
- **Prowlarr API Key** (`prowlarr_api_key`) — Ключ API для взаимодействия с индексаторами.
- **qBittorrent URL** (`qbit_url`) — Адрес установленного клиента qBittorrent.
- **qBittorrent Username** (`qbit_username`) — Логин qBittorrent.
- **qBittorrent Password** (`qbit_password`) — Пароль qBittorrent.

## Эндпоинты API
- `GET /api/categories` — получение категорий загрузок из qBittorrent.
- `GET /api/search?query=...` — поиск медиа в TMDb.
- `GET /api/releases?title=...&year=...` — поиск торрент-релизов через Prowlarr.
- `POST /api/download` — отправка выбранной раздачи на закачку в qBittorrent.
