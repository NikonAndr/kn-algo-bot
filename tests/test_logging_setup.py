import logging

import pytest

from utils.logging_setup import setup_logging


@pytest.fixture
def clean_root_logger():
    root = logging.getLogger()
    saved_handlers, saved_level = root.handlers[:], root.level
    yield
    for handler in root.handlers:
        if handler not in saved_handlers:
            handler.close()
    root.handlers, root.level = saved_handlers, saved_level


def test_discord_library_errors_reach_the_log_file(tmp_path, clean_root_logger):
    setup_logging(log_dir=tmp_path)

    # This is the exact logger discord.ext.tasks uses when a loop dies.
    logging.getLogger("discord.ext.tasks").error(
        "Unhandled exception in internal background task 'poll_loop'."
    )
    for handler in logging.getLogger().handlers:
        handler.flush()

    assert "poll_loop" in (tmp_path / "bot.log").read_text()


def test_setup_logging_is_idempotent(tmp_path, clean_root_logger):
    setup_logging(log_dir=tmp_path)
    count = len(logging.getLogger().handlers)

    setup_logging(log_dir=tmp_path)

    assert len(logging.getLogger().handlers) == count
