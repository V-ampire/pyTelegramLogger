from telegram_logger.handlers import MessageParamsMixin

from unittest.mock import patch


TOKEN = 'test-token'
chat_ids = [1, 2, 3]


class SuperTestClass:
    pass


class SampleHandler(MessageParamsMixin, SuperTestClass):
    pass


def test_init():
    handler = SampleHandler(chat_ids, TOKEN)
    assert handler.token == TOKEN
    assert handler.chat_ids == chat_ids
    assert handler.proxies == None
    assert handler.disable_web_page_preview == False
    assert handler.disable_notification == False
    assert handler.reply_to_message_id == None
    assert handler.reply_markup == None


@patch.object(SuperTestClass, '__init__')
def test_call_super_init(mock_init):
    handler = SampleHandler(chat_ids, TOKEN)
    assert mock_init.call_count == 1


def test__get_message_params():
    handler = SampleHandler(chat_ids, TOKEN, disable_web_page_preview=True,
                                disable_notification=True, reply_to_message_id=1)
    expected = {
        'disable_web_page_preview': True,
        'disable_notification': True,
        'reply_to_message_id': 1, 
    }
    params = handler._get_message_params()
    assert expected == params


def test_get_reply_markup():
    expected_markup = {'keyboard': []}
    handler = SampleHandler(chat_ids, TOKEN, reply_markup=expected_markup)
    assert handler.get_reply_markup() == expected_markup