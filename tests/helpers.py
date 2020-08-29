import logging

from faker import Faker
import sys
import time
from typing import Dict, Optional


class RecordingHandler(logging.NullHandler):

    def __init__(self, *args, **kwargs):
        super(RecordingHandler, self).__init__(*args, **kwargs)
        self.records = []

    def handle(self, record):
        """Keep track of all the emitted records."""
        self.records.append(record)


class TestException(Exception):
    msg = 'This is test exception for testing telegram_logger'


class BaseTest:
    """
    Ths class contains method for creating sample log records.
    """

    # Define params for creating test log records
    def setup(self):
        self.record_created = time.time()
        self.record_name = 'test'
        self.record_funcName = 'test_function'
        self.record_exc_info = self.get_exc_info()

    def get_exc_info(self, exc_type=TestException):
        """
        Return exc_info for exception.
        :param exc_type: Type of exception that will return.
        """
        try:
            raise exc_type(TestException.msg)
        except exc_type:
            return sys.exc_info()

    def create_record(self, attrs={}):
        """
        Create and return instance of logging.LogRecord:
        :attrs: attributes of log record.
        """
        record_attrs = {
            'created': self.record_created,
            'name': self.record_name,
            'funcName': self.record_funcName,
            'exc_info': self.record_exc_info, 
        }
        if attrs:
            record_attrs.update(attrs)
        return logging.makeLogRecord(record_attrs)


class MockResponse(object):
    """
    Fake response object of requests.
    """
    def __init__(self, text: Optional[str]=None, json: Optional[Dict]=None, 
                    status_code: int=200) -> None:
        """
        Инициализация.
        :optional text: Текст ответа
        :optional json: JSON ответа в виде словаря
        :optional status: Статус ответа
        """
        self.text = text
        self.json_ = json
        self.status_code = status_code

    @property
    def ok(self) -> bool:
        return self.status_code == 200
    

    def json(self) -> Optional[Dict]:
        return self.json_

    def raise_for_status(self) -> bool:
        return True



