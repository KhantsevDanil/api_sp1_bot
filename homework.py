
import json
import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv


load_dotenv()


PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
YANDEX_HOMEWORK_STATUS = (
    'https://praktikum.yandex.ru/api/user_api/homework_statuses/')
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
SERVER_NAME = (
    'https://praktikum.yandex.ru/api/user_api/homework_statuses/')
bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
logging.basicConfig(
    level=logging.INFO,
    filename='main.log',
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s'
)


def parse_homework_status(homework):
    """Функция отвечает за возратс клиенту
    правильно сформулированного ответа.
    В зависимости от параметра status вернёт
     разные варианты текста"""
    verdict_dict = {
        'rejected': 'К сожалению в работе нашлись ошибки.',
        'approved': 'Ревьюеру всё понравилось,'
                    ' можно приступать к следующему уроку.',
    }
    homework_name = homework.get('homework_name')
    verdict_key = homework.get('status')
    if homework_name is not None and verdict_key is not None:
        buffer = verdict_dict[verdict_key]
        return (f'У вас проверили работу '
                f'"{homework_name}"!\n\n{buffer}')
    else:
        return('боту пришли пустые данные')


def get_homework_statuses(current_timestamp):
    """Фукция возращает словарь,
        взятый с сервиса API Яндекс практикум.
        На основе констант, значение констант занесено в файл '.env',
        который должен лежать в одной директории с проектом,
        вывод осуществляется при помощи load_dotenv()
        Функция обрабатывает ошибки 401 Ошибку запроса
        и ошибку не правильного формата json.
        При возникновении какой либо ошибки в телеграм бот выведет сообщение,
        соотвутствующее ошиьке"""
    if current_timestamp is None:
        current_timestamp = int(time.time())
    params = {'from_date': current_timestamp}

    try:
        homework_statuses = requests.get(
            url=SERVER_NAME,
            headers=HEADERS,
            params=params
        )
    except requests.exceptions.RequestException:
        logging.error('Request exception occurred', exc_info=True)
        raise('Request exception occurred')
    try:
        YP_request = homework_statuses.json()
    except json.decoder.JSONDecodeError:
        logging.error('JSONDecodeError occurred', exc_info=True)
        raise('JSONDecodeError occurred')
    if 'error' in YP_request:
        logging.error(YP_request['error'])
        raise(YP_request['error'])
    return YP_request


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    """Функция опрашивает цикл раз в 300 секнуд,
     на каждой итерациицикла обновляется
      переменная current_timestamp"""
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(parse_homework_status(
                    new_homework.get('homeworks')[0]))
            current_timestamp = new_homework.get(
                'current_date', current_timestamp)
            time.sleep(300)

        except Exception as e:
            print(f'Бот столкнулся с ошибкой: {e}')
            time.sleep(5)


if __name__ == '__main__':
    main()
