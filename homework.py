import logging
import os
import time
from json import JSONDecodeError

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
    homework_name = homework.get('homework_name')
    if homework_name is None:
        logging.error(f'В ответе сервера нет имени домашки: {homework_name}')
        return 'В ответе сервера нет имени домашки'
    homework_status = homework.get('status')
    if homework_status is None:
        logging.error(f'Статуса нет в ответе сервера: {homework_status}')
        return 'Статуса нет в ответе сервера'
    homework_checked = f'У вас проверили работу "{homework_name}"!\n\n'
    status_answers = {
        'reviewing': f'Работа "{homework_name}" взята на ревью',
        'rejected': (f'{homework_checked}'
                     'К сожалению в работе нашлись ошибки.'),
        'approved': (f'{homework_checked}'
                     'Ревьюеру всё понравилось, '
                     'можно приступать к следующему уроку.')
    }
    logging.info(homework)
    try:
        verdict = status_answers[homework_status]
        return f'{homework_checked} {verdict}'
    except KeyError:
        logging.exception('Неизвестное значение статуса')
        raise


def get_homework_statuses(current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    params = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(
            API_URL,
            headers=headers, params=params)
        return homework_statuses.json()
    except requests.RequestException:
        logging.error(f'Ошибка при обращении к API, параметры: {params}')
        return {}
    except JSONDecodeError:
        logging.info('Ошибка конвертации в JSON')
        return {}


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
            logging.exception('bot is down')
            send_message(
                f'Бот столкнулся с ошибкой: {e}', bot_client)
            time.sleep(5)


if __name__ == '__main__':
    main()
