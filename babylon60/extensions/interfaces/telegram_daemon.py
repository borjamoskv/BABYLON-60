# [C5-REAL] Exergy-Maximized
"""
C5-REAL: Telegram Antigravity Daemon
Connects the Telegram API to the local CORTEX-Persist engine.
Enforces Identity Hygiene via Whitelist.
"""

import logging
import os

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from babylon60.engine import CortexEngine

# Configure logging (C5-REAL Zero Noise)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger("Antigravity-Telegram")

WHITELIST_ENV = os.environ.get("CORTEX_TELEGRAM_WHITELIST", "")
AUTHORIZED_USERS = {int(uid.strip()) for uid in WHITELIST_ENV.split(",") if uid.strip().isdigit()}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id  # pyright: ignore[reportOptionalMemberAccess]
    if user_id not in AUTHORIZED_USERS:
        logger.warning("UNAUTHORIZED ACCESS ATTEMPT from ***id")
        return

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🦅 CORTEX-Antigravity Enlace Establecido. (C5-REAL)",  # pyright: ignore[reportOptionalMemberAccess]
    )


async def handle_instruction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id  # pyright: ignore[reportOptionalMemberAccess]
    if user_id not in AUTHORIZED_USERS:
        return

    instruction = update.message.text  # pyright: ignore[reportOptionalMemberAccess]
    logger.info("Instruction received: %s...", instruction[:50])  # pyright: ignore[reportOptionalSubscript]

    status_msg = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="⚙️ Procesando en matriz local...",  # pyright: ignore[reportOptionalMemberAccess]
    )

    try:
        engine = CortexEngine()
        engine.memory.record(f"TELEGRAM_INTENT: {instruction}", "Local execution requested via TG.")  # pyright: ignore[reportOptionalMemberAccess]

        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,  # pyright: ignore[reportOptionalMemberAccess]
            message_id=status_msg.message_id,
            text="✅ Ejecutado. Instrucción procesada en Engine local.",
        )
    except (ValueError, TypeError, KeyError, RuntimeError, OSError, AssertionError) as e:  # noqa: BLE001
        logger.error("Execution failed: %s", e)
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,  # pyright: ignore[reportOptionalMemberAccess]
            message_id=status_msg.message_id,
            text=f"❌ Fallo de ejecución local: {e!s}",
        )


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN missing in environment. Aborting.")
        return

    if not AUTHORIZED_USERS:
        logger.error(
            "CORTEX_TELEGRAM_WHITELIST is empty. Identity hygiene requires at least 1 authorized UID."
        )
        return

    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_instruction))

    logger.info(
        "Starting Antigravity Telegram Daemon for %s authorized sovereign(s)...",
        len(AUTHORIZED_USERS),
    )
    application.run_polling()


if __name__ == "__main__":
    main()
