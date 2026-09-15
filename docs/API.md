# Документация API

## Система (System)
- `GET /api/system/setup-status`: Требуется ли первоначальная настройка.
- `GET/PUT /api/system/settings`: Управление глобальными системными настройками.

## Аутентификация (Auth)
- `POST /api/auth/setup`: Создание первого администратора.
- `POST /api/auth/login`: Получение JWT-токена для входа.

## Плагины (Plugins)
- `GET /api/plugins`: Получить список всех установленных плагинов и их статусы.
- `POST /api/plugins/install`: Загрузка и установка `.hm` архива плагина.
- `POST /api/plugins/{id}/start`: Запустить плагин.
- `POST /api/plugins/{id}/stop`: Остановить плагин.
- `POST /api/plugins/{id}/restart`: Перезапустить плагин.
- `GET /api/plugins/{id}/config`: Получить текущие настройки плагина.
- `PUT /api/plugins/{id}/config`: Сохранить новые настройки плагина.
- `GET /api/plugins/{id}/schema`: Получить JSON-схему настроек из манифеста плагина.

## Проксирование (Proxy)
- `GET/POST/PUT/DELETE /proxy/{plugin_name}/{path:path}`: Проксирование HTTP-запросов к интерфейсу/API плагина.
- `WS /proxy/{plugin_name}/{path:path}`: Проксирование WebSocket-соединений к плагину.
