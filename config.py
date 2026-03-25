import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Часы, когда бот активен
# Например 20:00 - 09:00 для ночного режима
BOT_ACTIVE_START_HOUR = int(os.getenv("BOT_ACTIVE_START_HOUR", "20"))
BOT_ACTIVE_END_HOUR = int(os.getenv("BOT_ACTIVE_END_HOUR", "9"))

# Часовой пояс
TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")

SERVICES = [
    "Консультация",
    "Профгигиена",
    "Лечение кариеса",
    "Удаление зуба",
]

MOCK_SLOTS = {
    "Консультация": [
        "Сегодня 20:30",
        "Сегодня 21:15",
        "Завтра 08:30",
    ],
    "Профгигиена": [
        "Сегодня 20:45",
        "Завтра 08:00",
        "Завтра 08:45",
    ],
    "Лечение кариеса": [
        "Сегодня 21:00",
        "Завтра 09:00",
        "Завтра 09:30",
    ],
    "Удаление зуба": [
        "Сегодня 20:15",
        "Сегодня 21:30",
        "Завтра 08:15",
    ],
}
