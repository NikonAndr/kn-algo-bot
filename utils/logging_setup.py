import logging
import os
from logging.handlers import RotatingFileHandler

import discord

LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
FILE_HANDLER_NAME = "kn-algo-bot-file"


def setup_logging(log_dir="logs", level=logging.INFO):
    """Send all log records (ours and discord.py's) to stderr and logs/bot.log.

    bot.start() doesn't configure logging the way bot.run() does, and
    discord.py ships a NullHandler, so without this its errors - including
    "Unhandled exception in internal background task" - are silently dropped.
    """
    root = logging.getLogger()

    if any(handler.get_name() == FILE_HANDLER_NAME for handler in root.handlers):
        return

    # stderr -> systemd journal
    discord.utils.setup_logging(level=level, root=True)

    os.makedirs(log_dir, exist_ok=True)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "bot.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.set_name(FILE_HANDLER_NAME)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root.addHandler(file_handler)
