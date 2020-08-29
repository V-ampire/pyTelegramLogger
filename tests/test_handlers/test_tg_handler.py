from telegram_logger.handlers import TelegramHandler

import logging
from threading import active_count
from unittest.mock import patch


TOKEN = 'test-token'
chat_ids = [1, 2, 3]


def test_init_handler():
    handler = TelegramHandler(chat_ids, TOKEN)
    assert handler.listener.queue.maxsize == -1
    assert active_count() == 2


def test_set_unexpected_class_of_fromatter(caplog):
    handler = TelegramHandler(chat_ids, TOKEN)
    formatter = logging.Formatter()
    handler.setFormatter(formatter)
    assert handler.FORMATTER_WARNING in caplog.text
    assert handler.handler.formatter == formatter


def test_stop_listener():
    handler = TelegramHandler(chat_ids, TOKEN)
    with patch.object(handler.listener, 'stop') as mock_stop:
        handler.close()
        assert mock_stop.call_count == 1
