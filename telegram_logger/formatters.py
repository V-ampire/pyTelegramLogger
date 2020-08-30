import html
import logging
from typing import List, Optional


class TelegramFormatter(logging.Formatter):
    """
    Base class for formatters for telegram.
    """
    # Max message size for telegram message
    MAX_MESSAGE_SIZE = 4096
    # Parse mode
    PARSE_MODE = None  # type: Optional[str]

    def format_by_fragments(self, record: logging.LogRecord, start: int=0) -> List[str]:
        """
        Define there how to send message if message length > MAX_MESSAGE_SIZE.
        :param record: log record instance
        :optional start: Start char for splitting

        """
        raise NotImplementedError


class TelegramHtmlFormatter(TelegramFormatter):
    """
    Class to format log record in html format for message.
    """
    START_CODE = "<pre>"
    END_CODE = '</pre>'
    PARSE_MODE = 'html'

    def get_hashtag_for_record(self, record: logging.LogRecord) -> str:
        """
        Generate hashtag for log record.
        :param record: Log record.

        :return: Hashtag with logger name, function name and time.
        """
        return f"\n\n#{int(record.created)}.{record.name}.{record.funcName}"

    def _mark_code(self, code_text: str) -> str:
        """
        Put text of code in block code tag
        :param code_text: Text of code for message.
        """
        return f"{self.START_CODE}{html.escape(code_text)}{self.END_CODE}"

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record to markdown text for message.
        :param record: log record instance
        """
        description = ""
        if record.exc_info:
            description = self._mark_code(self.formatException(record.exc_info))
        timestamp = self.formatTime(record)

        return "<b>{levelname}</b>\n\n{timestamp}: {msg}\n\n{description}".format(
            levelname=record.levelname,
            timestamp=timestamp,
            msg=html.escape(record.getMessage()),
            description=description
        )

    def format_by_fragments(self, record: logging.LogRecord, start: int=0) -> List[str]:
        """
        Format and split formatted log record on fragments if text of record > MAX_MESSAGE_SIZE.
        There are some assumptions for format of message that splits:
        - there is just one block of code - traceback
        - length of block of information about logging event less than MAX_MESSAGE_SIZE.
        Append in each fragment hashtag based on current record.
        :param record: log record instance
        :optional start: Start char for splitting
        """
        message = self.format(record)
        if len(message) <= self.MAX_MESSAGE_SIZE:
            return [message]
        # Else split on fragments
        tag = self.get_hashtag_for_record(record)
        end = message.find(self.START_CODE, start)

        fragments = []
        # Append block of information about logging event
        fragments.append(f"{message[start:end]}{tag}")

        start = end
        end += self.MAX_MESSAGE_SIZE - len(tag) - len(self.END_CODE)
        code_fragment = message[start:end]

        while code_fragment:
            code_fragment = code_fragment.strip(self.START_CODE).strip(self.END_CODE)
            fragments.append(f"{self._mark_code(code_fragment)}{tag}")

            start = end
            end += self.MAX_MESSAGE_SIZE - len(tag) - len(self.START_CODE) - len(self.END_CODE)
            code_fragment = message[start:end]

        return fragments
