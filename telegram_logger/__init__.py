import logging

from .handlers import TelegramHandler, TelegramMessageHandler, TelegramStreamHandler
from .formatters import TelegramHtmlFormatter

from .__version__ import __version__


# configure root logger
root_logger = logging.getLogger()
formatter = logging.Formatter('telegram_logger : %(levelname)s: %(module)s: %(message)s')
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
root_logger.setLevel(logging.INFO)
root_logger.addHandler(handler)
