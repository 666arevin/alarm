from flask import Flask, request
from pathlib import Path
from datetime import datetime, timedelta
import json
from utils import str_to_bool
import sys
from flask_caching import Cache

# базовые директории
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# добавляем основную директорию для корректного импорта
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# настраиваем приложение и его кэш
app = Flask(__name__)
cache = Cache(app, config={"CACHE_TYPE": "SimpleCache"})

# кеш для хранения данных радара
cache.set("radar_data", {})

# время последнего сообщения, изначально минимальное
last_message_time = datetime.min.isoformat()

# наличие ошибок при получение данных от радара
cache.set("was_error", False)

@app.route("/alarm/v1/NewData", methods=["POST"])
def was_new_data():

    message_time: str = request.args.get("data")

    # если появились новые сообщения
    if message_time > last_message_time:
        cache.set("last_message_time", message_time)

        # обновляем даныне в кэше
        with open(DATA_DIR / "radar_data_proc.json", mode="r", encoding="utf-8") as f:
            radar_data = json.load(f)

        # получаем точко, которая была ровно час назад
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
def was_radar_error():
    global was_error

    # получаем данные из url
    url_args = request.args.get("data")
    was_error = str_to_bool(url_args)

    return "OK", 200


@app.route("/alarm/v1/products", methods=["POST"])
def post_products():

    global radar_data_cache

    url_data = request.args
    last_message = url_data.get("last_mes")

    last_mes_time = datetime.fromisoformat(last_message)
    time_now = datetime.now().astimezone()

    with open(DATA_DIR / "last_message.txt", "r", encoding="utf-8") as f:
        radar_data: dict = json.load(f)

    # конвертируем в нужный тип данных
    

    # собираем словарик с новымми данными
    filtered_data = {
        key: value
        for key, value in radar_data.items()
        if datetime.fromisoformat(key) > last_mes_time
    }






if __name__ == "__main__":
    app.run(port=9678)

