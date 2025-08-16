import os

# URL подключения к PostgreSQL (Railway его выдаст в переменных окружения)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://username:password@host:port/dbname"
)

# Хост и порт сервера
HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", 8000))  # Railway сам передаёт PORT

# Вкл/выкл логов
DEBUG = True
