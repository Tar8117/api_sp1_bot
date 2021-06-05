import logging
import os
import time
import requests

import telegram
from telegram.error import TelegramError
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s::%(levelname)s::%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
API_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
bot = telegram.Bot(token=TELEGRAM_TOKEN)


def parse_homework_status(homework):
    try:
        homework_name = homework.get('homework_name')
        homework_status = homework.get('status')
    except KeyError as e:
        raise Exception(
            f'неправильное значение {e}')
    homework_checked = f'У вас проверили работу "{homework_name}"!\n\n'
    status_answers = {
        'reviewing': f'Работа "{homework_name}" взята на ревью',
        'rejected': (f'{homework_checked}'
                     'К сожалению в работе нашлись ошибки.'),
        'approved': (f'{homework_checked}'
                     'Ревьюеру всё понравилось, '
                     'можно приступать к следующему уроку.')
    }
    try:
        return status_answers[homework_status]
    except KeyError as e:
        raise Exception(f'неизвестный статус: {e}')


def get_homework_statuses(current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    params = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(
            f'{API_URL}homework_statuses/',
            headers=headers, params=params)
    except Exception as e:
        raise Exception(f'Ошибка при обращении к API: {e}')
    return homework_statuses.json()


def send_message(message, bot_client):
    logging.info('Отправка сообщения пользователю. '
                 f'ID пользователя: {CHAT_ID}.'
                 f'Сообщение: {message}')
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    try:
        bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    except TelegramError as e:
        logging.error(f'Бот не запущен: {e}')
        return
    logging.debug('Бот запущен')
    current_timestamp = int(time.time())
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(
                        new_homework.get('homeworks')[0]
                    ),
                    bot_client
                )
            current_timestamp = new_homework.get(
                'current_date', current_timestamp
            )
            time.sleep(300)

        except Exception as e:
            print(f'Бот столкнулся с ошибкой: {e}')
            time.sleep(5)


if __name__ == '__main__':
    main()
