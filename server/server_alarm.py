from flask import Flask, request, jsonify
from pathlib import Path
from datetime import datetime, timedelta
import json
from utils import str_to_bool
from typing import Any
import sys
from flask_caching import Cache
import logging
from logging.config import dictConfig
from threading import Thread
import time

# базовые директории
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# добавляем основную директорию для корректного импорта
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# настраиваем приложение и его кэш
app = Flask(__name__)
cache = Cache(
    app,
    config={
        "CACHE_TYPE": "SimpleCache",
        "CACHE_DEFAULT_TIMEOUT": 0,
        },
)

# настраивавем логгер
with open(DATA_DIR / "log_settings.jsonc", mode="r", encoding="utf-8") as f:
    LOGGER_CONFIG = json.load(f)
    
# добавляем путь для сохранения логов
LOGGER_CONFIG["handlers"]["file"]["filename"] = str(DATA_DIR / "server.log")

# запускаем логгер    
dictConfig(LOGGER_CONFIG)
logger = logging.getLogger()

# спец флаг, проверяет работает ли data_collector
cache.set("data_collector_alive", False)
# храним последение время, когда data_collector подтверждал работу
cache.set("last_heartbeat", (datetime.now().astimezone() - timedelta(minutes=3)))

# кеш для хранения данных радара
cache.set("radar_data", {})

# время последнего сообщения, изначально минимальное
cache.set("last_message_time", datetime.min.isoformat())

# наличие ошибок при получение данных от радара
cache.set("was_error", False)

def is_data_collector_alive() -> None:
    """Функция каждую минуту проверят, работает ли data_collector.
    Он проверяет что последние сообщение от него было не позже
    2 минут. Иначе меняет флаг data_collector_alive на False

    Return:
        None
    """

    while True:

        # получаем время последнего heartbeat от сервера
        last_heartbeat = cache.get("last_heartbeat")
        current_time = datetime.now().astimezone()

        # если время последнего heartbeat было давнее 2 минут
        if current_time - timedelta(minutes=2) > last_heartbeat:
            cache.set("data_collector_alive", False)
        else:
            cache.set("data_collector_alive", True)

        # логируем перменную data_collector_alive
        alive = cache.get("data_collector_alive")
        logging.debug(
            msg=f"data_collector доступеен -> {alive}"
        )

        # логируем, были ли загруженны данные в кэш
        is_data = True if cache.get("radar_data") else False
        logging.debug(
            f"Данные от радара есть -> {is_data}"
        )

        # ждем минуту перед следующей проверкой
        time.sleep(60)

# запускаем функцию проверки в отдельном потоке
th1 = Thread(target=is_data_collector_alive, daemon=True)
th1.start()


@app.route("/alarm/v1/IsAlive", methods=["POST"])
def keep_alive() -> tuple[str, int]:
    """Функция срабатывает когда data_collector подтверждает 
    что успешно отработал. Функция сохраняет в кэш время этого
    подтверждения

    Returns:
        tuple[str, int]: Возвращает статус что все хорошо.
    """

    # получаем время, когда data_collector подтвердил что работает
    last_heartbeat = datetime.now().astimezone()
    cache.set("last_heartbeat", last_heartbeat)

    return "ОК", 200
    

@app.route("/alarm/v1/NewData", methods=["POST"])
def was_new_data() -> tuple[str, int]:
    """Проверяет актуальность данных. Сравнивает время последнего сообщения
    с закэшированным и перезаписывает кэш, если полученное время более новое.

    Returns:
        tuple[str, int]: Возвращает статус.
    """

    # получаем время последнего сообщения из url
    message_time: str = request.args.get("data")
    # берем время которое было записанно
    last_message_time = cache.get("last_message_time")

    # если появились новые сообщения
    if message_time > last_message_time:
        cache.set("last_message_time", message_time)

        # загружаем данные радара из файла
        with open(DATA_DIR / "radar_data_proc.json", mode="r", encoding="utf-8") as f:
            radar_data: dict = json.load(f)

        # получаем точку, которая была ровно час назад
        # все сообщения после нее нам надо загрузить в кэш
        current_time = datetime.now().astimezone()
        hour_ago = (current_time - timedelta(minutes=60)).isoformat()

        # получаем все нужные сообщения, давностью не более часа
        radar_data_filtered= {
            key: value
            for key, value in radar_data.items()
            if key > hour_ago
        }

        # записываем в кэш
        cache.set("radar_data", radar_data_filtered)

    return "ОК", 200

@app.route("/alarm/v1/GetDataError", methods=["POST"])
def was_radar_error() -> tuple[str, int]:
    """Функция отслеживает, был ли потерян доступ к радару или нет.
    Эту информацию она сохраняет в кэш.

    Returns:
        str, int: Возвращает статус.
    """

    # получаем данные из url
    url_args = request.args.get("data")
    cache.set("was_error", str_to_bool(url_args))

    return "OK", 200


@app.route("/alarm/v1/Products", methods=["POST"])
def post_products():

    # берем данные из кэша
    radar_data_cache: dict = cache.get("radar_data")
    # время после которого пользователю нужны данные
    last_message = request.args.get("last_message")

    # если была ошибка при получения данных от радара
    if cache.get("was_error"):
        msg = "Failed to receive data from the radar"
        return msg, 501

    # жив ли сервер, и загрузили ли данные
    elif not cache.get("data_collector_alive") or not radar_data_cache:
        msg = "The server is not running, or no data available"
        return msg, 202


    # если все отработало без ошибок
    else:
        # только те данные которые нужно отправить пользователю
        filtered_data = {
            key: value
            for key, value in radar_data_cache.items()
            if key > last_message
        }

        return jsonify(filtered_data), 200


if __name__ == "__main__":
    app.run(port=9678, host="0.0.0.0")

