"""
Test for sending log message to telegram
"""
import logging
from logging.config import dictConfig
from environs import Env
import requests


env = Env()
env.read_env()


TOKEN = env('TG_TOKEN')
CHAT_IDS = env.list('CHAT_IDS')


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'telegram': {
            'class': 'telegram_logger.TelegramStreamHandler',
            'chat_ids': CHAT_IDS,
            'token': TOKEN,
            'level': 'INFO',
        },
    },
    'loggers': {
        'telegram': {
            'handlers': ['telegram'],
            'level': 'INFO',
        }
    }
}


dictConfig(LOGGING)

logger = logging.getLogger('telegram')


def test():
    print(f'Start sending log messages to telegram to chats: {",".join(CHAT_IDS)}')

    logger.info('This is info message to telegram_logger')
    print('INFO message is sent!')

    logger.warning('This is warning message to telegram_logger')
    print('WARNING message is sent!')

    logger.error('This is error message to telegram_logger')
    print('ERROR message is sent!')

    try:
        1/0
    except ZeroDivisionError as e:
        logger.exception(e, stack_info=True)
        print('EXCEPTION message is sent!')

    logger.critical('This is critical message to telegram_logger')
    print('CRITICAL message is sent!')

    print('All messages is sent! Please check your chats with logging bot!')


if __name__ == '__main__':
    test()