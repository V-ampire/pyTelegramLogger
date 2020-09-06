# pyTelegramLogger

## Description
This package provides handlers to send logging messages to telegram chats. It uses a separate thread for handling messages (see [logging.QueueHandler](https://docs.python.org/3/library/logging.handlers.html#queuehandler) for details). You can send messages to multiple chats, including big messages (over 4096 chars). Big messages will be split into several parts and tagged by unique hashtag for current log record.

## Installation

## Usage

1. Configure logger
```
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'telegram': {
            'class': 'telegram_logger.TelegramHandler',
            'chat_ids': [123456, 123456789],
            'token': 'bot_token,
        },
    },
    'loggers': {
        'telegram': {
            'handlers': ['telegram'],
        }
    }
}
```

2. Usage
```
# Run once at startup:
logging.config.dictConfig(LOGGING_CONFIG)

# Include to send logging messages to telegram
logger = logging.getLogger('telegram')

logger.warning('Warning message!')
```

## FAQ

### 1. Can I use my own formatter class for messages?

Yes you can. You can inherit from base class `telegram_logger.TelegramFormatter` and define how to send big messages (over 4096 chars) in method `format_by_fragments(self, record: logging.LogRecord, start: int=0) -> List[str]`.
Also you can use your own formatter class.
Then configure using standart configuration dictionary schema:
```
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'myFormattrer': {
            'class': 'MyFormatterClass',
            'fmt': '%(levelname)_%(name) : %(funcName)'
        }
    }
    'handlers': {
        'telegram': {
            'class': 'telegram_logger.TelegramHandler',
            'chat_ids': [123456, 123456789],
            'token': 'bot_token,
            'formatter': 'myFormattrer',
        },
    },
    'loggers': {
        'telegram': {
            'handlers': ['telegram'],
        }
    }
}
```


### 2. What if I don't want to send messages to telegram during development?

Sometimes, when you just develope you app and you dont want to send log messages to telegram, but want to control - use `telegram_logger.TelegramStreamHandler(cht_ids, token, stream=None)` which streams dict with message text and params instead of send it to telegram.


### 3. Can I use a proxy for sending messages?

Yes you can. You can specify proxy in key of config `proxies` using dict format as [requests](https://requests.readthedocs.io/en/master/):

```
proxies = {
  'http': 'http://10.10.1.10:3128',
  'https': 'http://10.10.1.10:1080',
}

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'telegram': {
            'class': 'telegram_logger.TelegramHandler',
            'chat_ids': [123456, 123456789],
            'token': 'bot_token,
            'proxies': proxies,
        },
    },
    'loggers': {
        'telegram': {
            'handlers': ['telegram'],
        }
    }
}
```
