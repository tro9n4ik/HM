# API Документация

## System
- `GET /api/system/setup-status`: Требуется ли первоначальная настройка.
- `GET/PUT /api/system/settings`: Управление системными настройками.

## Auth
- `POST /api/auth/setup`: Создание первого администратора.
- `POST /api/auth/login`: Получение JWT токена.

## Plugins
- `GET /api/plugins`: Список плагинов.
- `POST /api/plugins/install`: Загрузка `.hm` файла.
- `POST /api/plugins/{id}/start|stop`: Управление состоянием плагина.
