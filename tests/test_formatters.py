from telegram_logger.formatters import TelegramHtmlFormatter

from tests.helpers import BaseTest

import logging
from faker import Faker
import pytest
from unittest.mock import patch, Mock


fake = Faker()


class TestTelegramHtmlFormatter(BaseTest):

    def setup(self):
        super().setup()
        self.formatter = TelegramHtmlFormatter()
        self.record = self.create_record()

    def test_get_hashtag_for_record(self):
        expected = f"\n\n#{int(self.record.created)}.{self.record.name}.{self.record.funcName}"
        assert expected == self.formatter.get_hashtag_for_record(self.record)

    def test_mark_code(self):
        code_text = 'some code'
        assert self.formatter._mark_code(code_text).startswith(self.formatter.START_CODE)
        assert self.formatter._mark_code(code_text).endswith(self.formatter.END_CODE)

    @patch('telegram_logger.formatters.html.escape')
    def test_escaping_code(self, mock_escape):
        code_text = 'some code'
        self.formatter._mark_code(code_text)
        assert mock_escape.call_count == 1
        assert code_text in list(mock_escape.call_args)[0]

    @patch('telegram_logger.formatters.TelegramHtmlFormatter.formatTime')
    def test_format_exc_info_not_none(self, mock_time):
        excpected_time = fake.time()
        mock_time.return_value = excpected_time

        expected = "<b>{levelname}</b>\n\n{timestamp}: {msg}\n\n{description}".format(
            levelname=self.record.levelname,
            timestamp=excpected_time,
            msg=self.record.getMessage(),
            description=self.formatter._mark_code(self.formatter.formatException(self.record.exc_info))
        )
        assert expected == self.formatter.format(self.record)

    @patch('telegram_logger.formatters.TelegramHtmlFormatter.formatTime')
    def test_format_exc_info_is_none(self, mock_time):
        excpected_time = fake.time()
        mock_time.return_value = excpected_time
        record = self.create_record({'exc_info': None})

        expected = "<b>{levelname}</b>\n\n{timestamp}: {msg}\n\n{description}".format(
            levelname=record.levelname,
            timestamp=excpected_time,
            msg=record.getMessage(),
            description=""
        )
        assert expected == self.formatter.format(record)

    @patch('telegram_logger.formatters.html.escape')
    def test_escape_message(self, mock_escape):
        record = self.create_record({'exc_info': None})
        self.formatter.format(record)
        assert mock_escape.call_count == 1
        assert record.getMessage() in list(mock_escape.call_args)[0]

    @patch('telegram_logger.formatters.TelegramHtmlFormatter.format')
    def test_format_by_fragments_message_less_max_size(self, mock_format, 
                                                message_less_max_message_size):
        mock_format.return_value = message_less_max_message_size
        fragments = self.formatter.format_by_fragments(self.record)

        assert len(fragments) == 1
        assert fragments[0] == message_less_max_message_size


    @patch('telegram_logger.formatters.TelegramHtmlFormatter.format')
    def test_format_by_fragments_message_more_max_size(self, mock_format, 
                                                message_splits_on_3_fragments):
        mock_format.return_value = message_splits_on_3_fragments
        fragments = self.formatter.format_by_fragments(self.record)
        start_code = message_splits_on_3_fragments.find(self.formatter.START_CODE)
        tag = self.formatter.get_hashtag_for_record(self.record)

        assert len(fragments) == 3
        assert fragments[0] == message_splits_on_3_fragments[0:start_code] + tag
        assert len(fragments[1]) <= self.formatter.MAX_MESSAGE_SIZE
        assert len(fragments[2]) <= self.formatter.MAX_MESSAGE_SIZE
        assert fragments[1].startswith(self.formatter.START_CODE)
        assert fragments[1].endswith(self.formatter.END_CODE + tag)
        assert fragments[2].startswith(self.formatter.START_CODE)
        assert fragments[2].endswith(self.formatter.END_CODE + tag)
      
        
