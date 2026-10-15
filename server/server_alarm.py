from flask import Flask, request
from pathlib import Path
from datetime import datetime, timedelta
import json
from utils import str_to_bool, rotating_save_json
import sys
from flask_caching import Cache
import requests

# базовые директории
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# добавляем основную директорию для корректного импорта
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# настраиваем приложение и его кэш
app = Flask(__name__)
cache = Cache(app, config={"CACHE_TYPE": "SimpleCache"})


# def upload_procc_data():
#     # время
#     current_time = datetime.now().astimezone()
#     hour_ago = (current_time - timedelta(minutes=60)).isoformat()

#     # создаем файл если он вдруг не существует
#     file_radar_data = DATA_DIR / "radar_data_proc.json"
#     if not file_radar_data.exists():
#         with open(file_radar_data, mode="w", encoding="utf-8") as f:
#             json.dump({}, f, indent=4, ensure_ascii=False)

#         return {}, datetime.min.isoformat()

#     # загружаем данные из файла
#     with open(DATA_DIR / "radar_data_proc.json", mode="r", encoding="utf-8") as f:
#         radar_data: dict = json.load(f)

#     # оставляе сообщения за послежний час
#     radar_data_filtered = {
#         key: value
#         for key, value in radar_data.items()
#         if key > hour_ago
#     }

#     # получаем время последнего сообщения
#     last_message_time = max(radar_data)

#     return radar_data_filtered, last_message_time

def is_data_collector_alive():


# кеш для хранения данных радара
cache.set("radar_data", )

# время последнего сообщения, изначально минимальное
cache.set("last_message_time", last_message_time)

# наличие ошибок при получение данных от радара
cache.set("was_error", False)


def keep_alive():
    

@app.route("/alarm/v1/NewData", methods=["POST"])
def was_new_data():

    # получаем время последнего сообщения из url
    message_time: str = request.args.get("data")

    # если появились новые сообщения
    if message_time > last_message_time:
        cache.set("last_message_time", message_time)

        # загружаем данные радара из файла
        with open(DATA_DIR / "radar_data_proc.json", mode="r", encoding="utf-8") as f:
            radar_data = json.load(f)

        # получаем точку, которая была ровно час назад
        # все сообщения после нее нам надо загрузить в кэш
        current_time = datetime.now().astimezone()
        hour_ago = (current_time - timedelta(minutes=60)).isoformat()

        # получаем все нужные сообщения, давностью не более часа
        radar_data_filtered= {
            key: value
            for key, value in radar_data
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


@app.route("/alarm/v1/products", methods=["POST"])
def post_products():

    # получаем от пользователя последние время сообщения, которые он уже получал
    url_data = request.args
    last_message = url_data.get("last_mes")

    # текущее время
    time_now = datetime.now().astimezone()

    radar_data_cache = cache.get("radar_data")

    if not radar_data_cache:
        requests.post(
            url="http://localhost:9678/alarm/v1/GetDataError",
            params={"data": True}
        )

    # собираем словарик с новымми данными
    filtered_data = {
        key: value
        for key, value in radar_data_cache.items()
        if datetime.fromisoformat(key) > last_mes_time
    }






if __name__ == "__main__":
    app.run(port=9678)

