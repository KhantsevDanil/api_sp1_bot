import os
import time
import requests, logger, json, telegram
from dotenv import load_dotenv
import logging
import telegram
from telegram import Bot

load_dotenv()


PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
YANDEX_HOMEWORK_STATUS = "https://praktikum.yandex.ru/api/user_api/homework_statuses/"
bot_client = telegram.Bot(token=TELEGRAM_TOKEN)

logging.basicConfig(
    level=logging.INFO,
    filename='main.log',
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s'
)

def parse_homework_status(homework):
    homework_name = homework["homework_name"]
    if homework["status"] == "rejected":
        verdict = 'К сожалению в работе нашлись ошибки.'
    else:
        verdict = 'Ревьюеру всё понравилось, можно приступать к следующему уроку.'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):

    server_name = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    params = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(
            url=server_name,
            headers=headers,
            params=params
        )
    except requests.exceptions.RequestException:
        logger.error('Request exception occurred', exc_info=True)
        send_message('Request exception occurred', bot_client)
        return {}
    try:
        YP_request = homework_statuses.json()
    except json.decoder.JSONDecodeError:
        logger.error('JSONDecodeError occurred', exc_info=True)
        send_message('JSONDecodeError occurred', bot_client)
        return {}
    if 'error' in YP_request:
        logger.error(YP_request['error'])
        send_message(YP_request['error'], bot_client)
    return YP_request


def send_message(message, bot_client):

    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    # проинициализировать бота здесь
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())  # начальное значение timestamp

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(parse_homework_status(new_homework.get('homeworks')[0]))
            current_timestamp = new_homework.get('current_date', current_timestamp)  # обновить timestamp
            time.sleep(300)  # опрашивать раз в пять минут

        except Exception as e:
            print(f'Бот столкнулся с ошибкой: {e}')
            time.sleep(5)


if __name__ == '__main__':
    main()
