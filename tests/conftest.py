from telegram_logger.formatters import TelegramHtmlFormatter

from faker import Faker
import pytest


fake = Faker()


@pytest.fixture()
def message_less_max_message_size():
    start_code = TelegramHtmlFormatter.START_CODE
    end_code = TelegramHtmlFormatter.END_CODE
    return "*{levelname}*\n\n{timestamp}: {msg}\n\n{description}".format(
        levelname = 'ERROR',
        timestamp = fake.iso8601(),
        msg = 'Sample error',
        description = f"{start_code}{fake.sentence()}{end_code}"
    )


@pytest.fixture()
def message_splits_on_3_fragments():
    start_code = TelegramHtmlFormatter.START_CODE
    end_code = TelegramHtmlFormatter.END_CODE
    description = fake.sentence()

    while len(description) < TelegramHtmlFormatter.MAX_MESSAGE_SIZE*1.5:
        description += f"\n{fake.sentence()}"
    
    return "*{levelname}*\n\n{timestamp}: {msg}\n\n{description}".format(
        levelname = 'ERROR',
        timestamp = fake.iso8601(),
        msg = 'Sample error',
        description = f"{start_code}{description}{end_code}"
    )