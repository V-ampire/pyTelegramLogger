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
    # FIXME Другие параметры для запроса.
    def __init__(self, chat_ids: List[str], token: str, proxies: Optional[Dict[str, str]]=None,
                    disable_web_page_preview: bool=False, disable_notification: bool=False,
                    reply_to_message_id: Optional[int]=None,
                    reply_markup: Optional[Dict[str, Any]]=None) -> None:
        """
        Initialization.
        :param token: Telegram token.
        :optional proxy: Proxy for requests. Supports only https or socks5 proxy.
        """
        self.queue = Queue(-1)
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
        self.handler.setFormatter(TelegramHtmlFormatter())
        self.listener = QueueListener(self.queue, self.handler)
        self.listener.start()

    def setFormatter(self, formatter):
        """
        Set formatter to handler.
        """
        if not isinstance(formatter, TelegramFormatter):
            logger.warning(self.FORMATTER_WARNING)
        self.handler.setFormatter(formatter)

    def prepare(self, record):
        return record

    def close(self):
        """
        Wait till all records will be processed then stop listener.
        """
        self.listener.stop()
        super().close()


class MessageParamsMixin(object):
    """
    Mixin class with initialization and methods to prepare message for sending to telegram.
    """    
    def __init__(self, chat_ids: List[str], token: str,
                    proxies: Optional[Dict[str, str]]=None, 
                    disable_web_page_preview: bool=False,
                    disable_notification: bool=False,
                    reply_to_message_id: Optional[int]=None,
                    reply_markup: Optional[Dict[str, Any]]=None, *args, **kwargs) -> None:        
        """
        Initialization.
        :param token: Telegram token.
        :optional proxy: Proxy for requests. Supports only https or socks5 proxy.
        """
        self.token = token
        self.chat_ids = chat_ids
        self.proxies = proxies
        self.disable_web_page_preview = disable_web_page_preview
        self.disable_notification = disable_notification
        self.reply_to_message_id = reply_to_message_id
        self.reply_markup = reply_markup
        super().__init__(*args, **kwargs)

    def _get_message_params(self) -> Dict[str, Any]:
        """
        Generate parameters for sending message.
        """ 
        params = {}
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

    def get_reply_markup(self) -> Dict[str, Any]:
        """
        Override this if you need to generate reply_markup.
        """
        return self.reply_markup



class TelegramMessageHandler(MessageParamsMixin, logging.Handler):
    """
    Handler that send log message to telegram admins chats.
    """
    def send_message(self, chat_id: str, text: str, parse_mode: Optional[str]=None) -> None:
        """
        Send message to telegram chat.
        :param chat_id: Telegram chat ID
        :param text: Text of message.
        :param parse_mode: Message format.
        """
        if not parse_mode:
            parse_mode = self.formatter.PARSE_MODE
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
        :param message: text for send.
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
        self.setFormatter(TelegramHtmlFormatter())

    def get_send_message_data(self, chat_id: str, text: str, 
                                parse_mode: Optional[str]=None) -> Dict[str, Any]:
        """
        Return data which would be used for sending message to telegram.
        """
        if not parse_mode:
            try:
                parse_mode = self.formatter.PARSE_MODE
            except AttributeError:
                parse_mode = None
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

    def emit(self, record: str) -> None:
        """
        Send message to telegram chats.
        If formatter is subclass of TelegramFormatter them emit message
        by fragments.
        :param message: text for send.
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
        







