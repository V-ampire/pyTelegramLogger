from telegram_logger.handlers import TelegramMessageHandler
from telegram_logger.formatters import TelegramHtmlFormatter

from tests.helpers import MockResponse

from faker import Faker
import logging
from unittest.mock import patch


fake = Faker()

TOKEN = 'test-token'
chat_ids = [1, 2, 3]


tg_handler = TelegramMessageHandler(chat_ids, TOKEN)


def test_default_formatter():
    assert isinstance(tg_handler.formatter, TelegramHtmlFormatter)


def test_send_message_got_error(caplog):
    response_text = 'Not Found'
    response_code = 404
    with patch('telegram_logger.handlers.requests.post') as mock_post:
        mock_post.return_value = MockResponse(status_code=response_code, text=response_text)
        tg_handler.send_message(1, 'lorem')
        assert str(response_code) in caplog.text
        assert response_text in caplog.text


@patch('telegram_logger.handlers.TelegramMessageHandler._process_response')
@patch('telegram_logger.handlers.requests.post')
def test_send_message_success(mock_post, mock_process):
    response_data = {'ok': True, 'message': fake.sentence()}
    mock_post.return_value = MockResponse(status_code=200, json=response_data)
    chat_id = '1'
    tg_handler.send_message(chat_id, 'lorem')
    assert mock_process.call_count == 1
    assert response_data in list(mock_process.call_args)[0]
    assert chat_id in list(mock_process.call_args)[0]


def test__process_response_fail(caplog):
    chat_id = '1'
    response_data = {'ok': False, 'description': fake.sentence()}
    tg_handler._process_response(chat_id, response_data)
    assert str(chat_id) in caplog.text
    assert response_data['description'] in caplog.text


def test__process_response_unexpected(caplog):
    chat_id = '1'
    response_data = {fake.word(): fake.sentence()}
    tg_handler._process_response(chat_id, response_data)
    assert str(response_data) in caplog.text


@patch('telegram_logger.handlers.TelegramMessageHandler.format')
@patch('telegram_logger.handlers.TelegramMessageHandler.send_message')
def test_emit_when_no_formatter(mock_send, mock_format):
    record = logging.makeLogRecord({})
    mock_format.return_value = record
    handler = TelegramMessageHandler(chat_ids, TOKEN)
    handler.formatter = None
    handler.emit(record)
    assert mock_format.call_count == len(chat_ids)
    assert mock_send.call_count == len(chat_ids)
    for chat_id, call in zip(chat_ids, mock_send.call_args_list):
        assert record in call.args
        assert chat_id in call.args


@patch('telegram_logger.handlers.TelegramMessageHandler.format')
@patch('telegram_logger.handlers.TelegramMessageHandler.send_message')
def test_emit_when_no_format_by_fragments(mock_send, mock_format):
    record = logging.makeLogRecord({})
    mock_format.return_value = record
    handler = TelegramMessageHandler(chat_ids, TOKEN)
    formatter = logging.Formatter()
    handler.setFormatter(formatter)
    handler.emit(record)
    assert mock_format.call_count == len(chat_ids)
    assert mock_send.call_count == len(chat_ids)
    for chat_id, call in zip(chat_ids, mock_send.call_args_list):
        assert record in call.args
        assert chat_id in call.args


@patch('telegram_logger.formatters.TelegramHtmlFormatter.format')
@patch('telegram_logger.handlers.TelegramMessageHandler.send_message')
def test_emit_success(mock_send, mock_format, message_splits_on_3_fragments):
    record = logging.makeLogRecord({})
    mock_format.return_value = message_splits_on_3_fragments
    expected_fragments = tg_handler.formatter.format_by_fragments(record)
    tg_handler.handle(record)
    assert mock_send.call_count == len(chat_ids)*len(expected_fragments)