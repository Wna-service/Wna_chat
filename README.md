# Messenger Server

Минимальный сервер для мессенджера (клон Telegram). Работает на Railway + PostgreSQL.

## Файлы
- `server.py` — основной сервер (FastAPI + WebSocket + PostgreSQL)
- `config.py` — настройки (БД, порт и т.п.)
- `requirements.txt` — зависимости
- `README.md` — документация

## Установка и запуск (локально)
```bash
pip install -r requirements.txt
python server.py
