import json
import logging
import os
import time

import requests

import logger
import telegram
from dotenv import load_dotenv

load_dotenv()


PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
YANDEX_HOMEWORK_STATUS = (
    "https://praktikum.yandex.ru/api/user_api/homework_statuses/")
bot_client = telegram.Bot(token=TELEGRAM_TOKEN)

logging.basicConfig(
    level=logging.INFO,
    filename="main.log",
    format="%(asctime)s, %(levelname)s, %(name)s, %(message)s"
)


def parse_homework_status(homework):
    """Функция отвечает за возратс клиенту
    правильно сформулированного ответа.
    В зависимости от параметра status вернёт
     разные варианты текста"""
    homework_name = homework["homework_name"]
    if homework["status"] == "rejected":
        verdict = "К сожалению в работе нашлись ошибки."
    else:
        verdict = "Ревьюеру всё понравилось, можно приступать к следующему уроку."
    return f"У вас проверили работу '{homework_name}'!\n\n{verdict}"


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

    server_name = "https://praktikum.yandex.ru/api/user_api/homework_statuses/"
    headers = {"'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'"}
    params = {"from_date": current_timestamp}
    try:
        homework_statuses = requests.get(
            url=server_name,
            headers=headers,
            params=params
        )
    except requests.exceptions.RequestException:
        logger.error("Request exception occurred", exc_info=True)
        send_message("Request exception occurred", bot_client)
        return {}
    try:
        YP_request = homework_statuses.json()
    except json.decoder.JSONDecodeError:
        logger.error("JSONDecodeError occurred", exc_info=True)
        send_message("JSONDecodeError occurred", bot_client)
        return {}
    if 'error' in YP_request:
        logger.error(YP_request["error"])
        send_message(YP_request["error"], bot_client)
    return YP_request


def send_message(message, bot_client):

    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    """начальное значение timestamp"""
    current_timestamp = int(time.time())
    """Фукция будет обращаться к серверу раз в 300 секунд,
     и при нахождении дз или ошибки вывожить соответсвующие сообщения.
     Функция обновляет таймер после каждого запроса к серверу"""
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get("homeworks"):
                send_message(parse_homework_status(
                    new_homework.get("homeworks")[0]))
            current_timestamp = new_homework.get(
                'current_date', current_timestamp)
            time.sleep(300)

        except Exception as e:
            print(f"Бот столкнулся с ошибкой: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
