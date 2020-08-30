from telegram_logger.handlers import TelegramStreamHandler
from telegram_logger.formatters import TelegramHtmlFormatter

from faker import Faker
import json
import logging
import io
from unittest.mock import patch


fake = Faker()


TOKEN = 'test-token'
chat_ids = [1, 2, 3]


class TestTelegramStreamHandler():

    def setup_method(self, method):
        self.stream = io.StringIO()
        self.tg_handler = TelegramStreamHandler(chat_ids, TOKEN, stream=self.stream)

    def teardown_method(self, method):
        self.stream.close()

    def test_default_formatter(self):
        assert isinstance(self.tg_handler.formatter, TelegramHtmlFormatter)


    def test_get_send_message_data(self):
        expected_chat_id = chat_ids[0]
        expected_message = fake.sentence()
        expected_params = self.tg_handler._get_message_params()
        expected_params.update({
            'chat_id': expected_chat_id,
            'text': expected_message,
            'parse_mode': self.tg_handler.parse_mode,
        })
        expected = {
            'url': self.tg_handler.url,
            'params': expected_params,
            'proxies': self.tg_handler.proxies
        }
        assert expected == self.tg_handler.get_send_message_data(expected_chat_id, expected_message)


    def test_emit_when_no_formatter(self):
        record = logging.makeLogRecord({'msg': 'Test record'})
        expected_message = self.tg_handler.format(record)
        expected_msg = ''
        for chat_id in chat_ids:
            expected_data = self.tg_handler.get_send_message_data(chat_id, expected_message)
            expected_msg = expected_msg + json.dumps(expected_data, ensure_ascii=False) + self.tg_handler.terminator
        self.tg_handler.emit(record)
        assert self.stream.getvalue() == expected_msg


    def test_emit_when_no_format_by_fragments(self):
        record = logging.makeLogRecord({'msg': 'Test record'})
        handler = TelegramStreamHandler(chat_ids, TOKEN, stream=self.stream)
        formatter = logging.Formatter()
        handler.setFormatter(formatter)
        expected_message = handler.format(record)
        expected_msg = ''
        for chat_id in chat_ids:
            expected_data = handler.get_send_message_data(chat_id, expected_message)
            expected_msg = expected_msg + json.dumps(expected_data, ensure_ascii=False) + handler.terminator
        handler.emit(record)
        assert self.stream.getvalue() == expected_msg


    @patch('telegram_logger.formatters.TelegramHtmlFormatter.format')
    def test_emit_success(self, mock_format, message_splits_on_3_fragments):
        record = logging.makeLogRecord({})
        mock_format.return_value = message_splits_on_3_fragments
        expected_fragments = self.tg_handler.formatter.format_by_fragments(record)
        expected_msg = ''
        for chat_id in chat_ids:
            for fragment in expected_fragments:
                expected_data = self.tg_handler.get_send_message_data(chat_id, fragment)
                expected_msg = expected_msg + json.dumps(expected_data, ensure_ascii=False) + self.tg_handler.terminator
        self.tg_handler.emit(record)
        assert self.stream.getvalue() == expected_msg



