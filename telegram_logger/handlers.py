from telegram_logger.formatters import TelegramHtmlFormatter, TelegramFormatter

import logging
from logging.handlers import QueueHandler, QueueListener
import json
from queue import Queue
import requests
from typing import Optional, Dict, Any, List


logger = logging.getLogger(__name__)


class TelegramHandler(QueueHandler):
    """
    Handler that takes telegram params.
    Instantiate queue and start listener.
    """
    # Message for setting unexpected class as formatter
    FORMATTER_WARNING = 'Formatter class is not subclass of telegram_logger.TelegramFormatter, \
its possible problems with sending long log message to telegram'

    def __init__(self, chat_ids: List[str], token: str, proxies: Optional[Dict[str, str]]=None,
                 disable_web_page_preview: bool=False, disable_notification: bool=False,
                 reply_to_message_id: Optional[int]=None,
                 reply_markup: Optional[Dict[str, Any]]=None) -> None:
        """
        Initialization.
        :param token: Telegram token.
        :optional proxies: Proxy for requests. Format proxies corresponds format proxies 
        in requests library.
        Parameters for message to telegram, see https://core.telegram.org/bots/api#sendmessage
        :optional disable_web_page_preview: Disables link previews for links in this message.
        :optional disable_notification: Sends the message silently. 
        Users will receive a notification with no sound.
        :optional reply_to_message_id: If the message is a reply, ID of the original message.
        :optional reply_markup: Additional interface options. 
        A JSON-serialized object for an inline keyboard, custom reply keyboard,
        instructions to remove reply keyboard or to force a reply from the user.
        """
        self.queue = Queue(-1)  # type: Queue
        super().__init__(self.queue)
        self.handler = TelegramMessageHandler(
            chat_ids,
            token,
            proxies=proxies,
            disable_web_page_preview=disable_web_page_preview,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup
        )
        # Set default formatter
        self.handler.setFormatter(TelegramHtmlFormatter())
        self.listener = QueueListener(self.queue, self.handler)
        self.listener.start()

    def setFormatter(self, formatter: logging.Formatter) -> None:
        """
        Set formatter to handler.
        :param formatter: Formatter instance.
        """
        if not isinstance(formatter, TelegramFormatter):
            logger.warning(self.FORMATTER_WARNING)
        self.handler.setFormatter(formatter)

    def prepare(self, record: logging.LogRecord) -> logging.LogRecord:
        """
        Prepare record.
        """
        return record

    def close(self) -> None:
        """
        Wait till all records will be processed then stop listener.
        """
        self.listener.stop()
        super().close()


class MessageParamsMixin(object):
    """
    Mixin class with initialization and methods to prepare message for sending to telegram.
    """
    # Warning message if formatter for handler has not parse mode
    PARSE_MODE_WARNING = f'Formatter for handler has not attribute PARSE_MODE, \
        its possible problems with sending message to telegram in correct format'

    def __init__(self, chat_ids: List[str], token: str,
                 proxies: Optional[Dict[str, str]]=None,
                 disable_web_page_preview: bool=False,
                 disable_notification: bool=False,
                 reply_to_message_id: Optional[int]=None,
                 reply_markup: Optional[Dict[str, Any]]=None, *args, **kwargs) -> None:
        """
        Initialization.
        :param chat_ids: List of telegram chats IDs for getting log messages.
        :param token: Telegram token.
        :optional proxies: Proxy for requests. Format proxies corresponds format proxies 
        in requests library.
        Parameters for message to telegram, see https://core.telegram.org/bots/api#sendmessage
        :optional disable_web_page_preview: Disables link previews for links in this message.
        :optional disable_notification: Sends the message silently. 
        Users will receive a notification with no sound.
        :optional reply_to_message_id: If the message is a reply, ID of the original message.
        :optional reply_markup: Additional interface options. 
        A JSON-serialized object for an inline keyboard, custom reply keyboard,
        instructions to remove reply keyboard or to force a reply from the user.
        """
        # https://github.com/python/mypy/issues/5887
        super().__init__(*args, **kwargs)  # type: ignore
        self.token = token
        self.chat_ids = chat_ids
        self.proxies = proxies
        self.disable_web_page_preview = disable_web_page_preview
        self.disable_notification = disable_notification
        self.reply_to_message_id = reply_to_message_id
        self.reply_markup = reply_markup

    @property
    def parse_mode(self) -> Optional[str]:
        """
        Return formatter parse mode.
        If formatter has not parse mode, then log warning message and return None.
        """
        formatter = self.formatter  # type: ignore
        if formatter:
            try:
                return formatter.PARSE_MODE
            except AttributeError:
                logger.warning(self.PARSE_MODE_WARNING)
        return None

    def _get_message_params(self) -> Dict[str, Any]:
        """
        Generate parameters for sending message.
        """
        params = {}  # type: Dict
        reply_markup = self.get_reply_markup()
        if reply_markup:
            params['reply_markup'] = reply_markup
        if self.reply_to_message_id:
            params['reply_to_message_id'] = self.reply_to_message_id
        if self.disable_web_page_preview:
            params['disable_web_page_preview'] = self.disable_web_page_preview
        if self.disable_notification:
            params['disable_notification'] = self.disable_notification
        return params

    @property
    def url(self) -> str:
        return f'https://api.telegram.org/bot{self.token}/sendMessage'

    def get_reply_markup(self) -> Optional[Dict[str, Any]]:
        """
        Override this if you need to generate reply_markup.
        """
        return self.reply_markup


class TelegramMessageHandler(MessageParamsMixin, logging.Handler):
    """
    Handler that send log message to telegram admins chats.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default formatter
        self.setFormatter(TelegramHtmlFormatter())

    def send_message(self, chat_id: str, text: str, parse_mode: Optional[str]=None) -> None:
        """
        Send message to telegram chat.
        :param chat_id: Telegram chat ID
        :param text: Text of message.
        :param parse_mode: Message format.
        """
        if not parse_mode:
            parse_mode = self.parse_mode
        params = self._get_message_params()
        params.update({
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode,
        })
        response = requests.post(self.url, json=params, proxies=self.proxies)
        if not response.ok:
            logger.warning(f'Request to telegram got error with code: {response.status_code}')
            logger.warning(f'Response is: {response.text}')
            return
        return self._process_response(chat_id, response.json())

    def emit(self, record: logging.LogRecord) -> None:
        """
        Send message to telegram chats.
        If formatter is subclass of TelegramFormatter them emit message
        by fragments.
        :param record: Instance of log record.
        """
        for chat_id in self.chat_ids:
            if self.formatter and isinstance(self.formatter, TelegramFormatter):
                for message in self.formatter.format_by_fragments(record):
                    self.send_message(chat_id, message)
            else:
                message = self.format(record)
                self.send_message(chat_id, message)

    def _process_response(self, chat_id: str, response: Dict[str, Any]) -> None:
        """
        Check response from telegram and log warning if response got error.
        :param chat_id: Telegram chat ID for sending log message.
        :param response: Response as dict from telegram.
        """
        try:
            if not response['ok']:
                logger.warning(f'Fail to send log message to chat {chat_id}: {response["description"]}')
        except KeyError:
            logger.warning(f'Unexpected response from telegram: {response}')


class TelegramStreamHandler(MessageParamsMixin, logging.StreamHandler):
    """
    Class for develope mode.
    This handler streams message which would be send to telegram.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default formatter
        self.setFormatter(TelegramHtmlFormatter())

    def get_send_message_data(self, chat_id: str, text: str,
                              parse_mode: Optional[str]=None) -> Dict[str, Any]:
        """
        Return data which would be used for sending message to telegram.
        :param chat_id: Telegram chat ID
        :param text: Text of message.
        :param parse_mode: Message format.
        """
        if not parse_mode:
            parse_mode = self.parse_mode
        params = self._get_message_params()
        params.update({
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode,
        })
        return {
            'url': self.url,
            'params': params,
            'proxies': self.proxies
        }

    def emit(self, record: logging.LogRecord) -> None:
        """
        Send message to telegram chats.
        If formatter is subclass of TelegramFormatter them emit message
        by fragments.
        :param record: Instance of log record.
        """
        try:
            stream = self.stream
            for chat_id in self.chat_ids:
                if self.formatter and isinstance(self.formatter, TelegramFormatter):
                    for message in self.formatter.format_by_fragments(record):
                        data = self.get_send_message_data(chat_id, message)
                        msg = json.dumps(data, ensure_ascii=False)
                        stream.write(msg + self.terminator)
                else:
                    message = self.format(record)
                    data = self.get_send_message_data(chat_id, message)
                    msg = json.dumps(data, ensure_ascii=False)
                    stream.write(msg + self.terminator)
            self.flush()
        except RecursionError:
            raise
        except Exception:
            self.handleError(record)
