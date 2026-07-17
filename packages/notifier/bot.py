import os
from pathlib import Path

from dotenv import load_dotenv
from telebot import TeleBot

# Implemented on the basis of: .venv\Lib\site-packages\telegram_notifier\bot.py


load_dotenv()  # loads Telegram secret credentials from .env
CHAT_ID = str(os.getenv("TELEGRAM_BOT_CHAT_ID"))
ACCESS_TOKEN = str(os.getenv("TELEGRAM_BOT_ACCESS_TOKEN"))


def send_file() -> None:
    tg_bot = TeleBot(ACCESS_TOKEN)
    file_path = Path(__file__).parent.joinpath("../../").joinpath("swagger-coverage-dm-api-account.html")

    # The report only exists after a successful --swagger-coverage run. If it is
    # missing (e.g. the test step failed before generating it), notify with a
    # text message instead of crashing on a missing file.
    if not file_path.is_file():
        tg_bot.send_message(
            CHAT_ID,
            text="⚠️ Swagger coverage report was not generated (the test run may have failed).",
        )
        return

    with open(file_path, "rb") as document:
        tg_bot.send_document(CHAT_ID, document=document, caption="swagger coverage report")


if __name__ == "__main__":
    send_file()
