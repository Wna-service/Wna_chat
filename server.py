import asyncio
import json
import logging
from typing import Dict

import asyncpg
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

from config import DATABASE_URL, HOST, PORT, DEBUG

app = FastAPI()

# Подключённые пользователи (ключ = addr, значение = WebSocket)
active_users: Dict[int, WebSocket] = {}

# Логгер
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


async def init_db():
    """Создание таблиц, если их ещё нет"""
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("""
    CREATE TABLE IF NOT EXISTS Users (
        IP TEXT,
        Nickname TEXT,
        ADDR SERIAL PRIMARY KEY
    );
    """)
    await conn.execute("""
    CREATE TABLE IF NOT EXISTS Messages (
        MADDR SERIAL PRIMARY KEY,
        Sender_ADDR INT,
        Message TEXT,
        Recipient_ADDR INT,
        Status CHAR(1)
    );
    """)
    await conn.close()


@app.on_event("startup")
async def startup():
    await init_db()
    logging.info("Database initialized")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Получаем данные о пользователе при подключении
        data = await websocket.receive_text()
        user_info = json.loads(data)
        nickname = user_info.get("nickname")
        ip = user_info.get("ip")

        # Регистрируем пользователя в БД
        addr = await conn.fetchval("""
            INSERT INTO Users (IP, Nickname) VALUES ($1, $2)
            RETURNING ADDR
        """, ip, nickname)

        active_users[addr] = websocket

        # Лог
        total_messages = await conn.fetchval("SELECT COUNT(*) FROM Messages")
        logging.info(f"User connected: {nickname} ({ip}) [ADDR={addr}]")
        logging.info(f"Online users: {len(active_users)} | Total messages: {total_messages}")

        # Слушаем входящие сообщения от клиента
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)

            sender_addr = addr
            recipient_addr = msg.get("recipient")
            message_text = msg.get("message")

            # Сохраняем сообщение в БД
            maddr = await conn.fetchval("""
                INSERT INTO Messages (Sender_ADDR, Message, Recipient_ADDR, Status)
                VALUES ($1, $2, $3, 'N') RETURNING MADDR
            """, sender_addr, message_text, recipient_addr)

            logging.info(f"user{sender_addr} ({ip}) send text \"{message_text}\" to user{recipient_addr}")

            # Пересылаем сообщение получателю, если он онлайн
            recipient_ws = active_users.get(recipient_addr)
            if recipient_ws:
                await recipient_ws.send_text(json.dumps({
                    "from": sender_addr,
                    "text": message_text,
                    "maddr": maddr
                }))
                await conn.execute("UPDATE Messages SET Status='Y' WHERE MADDR=$1", maddr)
            else:
                await conn.execute("UPDATE Messages SET Status='E' WHERE MADDR=$1", maddr)

    except WebSocketDisconnect:
        # Удаляем пользователя при отключении
        if addr in active_users:
            del active_users[addr]
        logging.info(f"User {nickname} ({ip}) disconnected")
    finally:
        await conn.close()


if __name__ == "__main__":
    uvicorn.run("server:app", host=HOST, port=PORT, reload=DEBUG)
      
