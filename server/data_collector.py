from requests.exceptions import RequestException
from requests import Session
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import re
from datetime import datetime, timedelta, timezone
from utils import *
import json
from logging.config import dictConfig
import logging


# основная папка
BASE_DIR = Path(__file__).resolve().parent
# тут лежат данные собранные из телеграмм канала
DATA_FOLDER = BASE_DIR / "data"

# настраивавем логгер
with open(DATA_FOLDER / "log_settings.jsonc", mode="r", encoding="utf-8") as f:
    LOGGER_CONFIG = json.load(f)
    
# добавляем путь для сохранения логов
LOGGER_CONFIG["handlers"]["file"]["filename"] = str(DATA_FOLDER / "app.log")

# запускаем логгер    
dictConfig(LOGGER_CONFIG)
logger = logging.getLogger()



class ServerErrorGetData(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        
        self.status_code = 404       

class FormatDataError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class DataAggregationService():
    def __init__(self):
        pass
        
    
    def get_radar_data(self, session: Session):
            
        flag_connection_error = 0
        
        # спец флаг, которые определяет, нужно ли сообщать серверу Flask
        # что подключение было восстановлено
        # False - подключение не было потеряно, сообщать не нужно
        # True - ранее были пробелемы с подключенем
        was_mistake = False
        
        # флаг, определяющий, знает ли локальный сервер о проблемах с доступом
        # к радару. Изначально сервер ничего не знает, пожтому False
        server_was_notified = False
        
        while True:
            try:
                # получаем основные данные
                response = session.get("https://t.me/s/radarrussiia", timeout=5)
                
                # если мы получили ответ от радара, сообщаем серверу если нужно
                # что подключение восстановленно
                if response.status_code == 200 and was_mistake == True:
                    server_was_notified = self.radar_is_available(error=False)
                    
                # возвращает не обработанный html
                main_body = response.text
                
                with open(DATA_FOLDER / "radar_data_raw.html", mode="w", encoding="utf-8") as f:
                    f.write(main_body)
                    
                return main_body
            
            # если произошла любая ошибка, из за которй не получили новые данные
            except RequestException:
                flag_connection_error += 1
                
                # если ошибка повторяется
                if flag_connection_error >= 4 and not server_was_notified:
                    
                    # отправляем локальному серверу Flask информацию об ошибке 
                    # при этом продолжаем попытки достучаться до радара
                    server_was_notified = self.radar_is_available(error=True)
                    was_mistake = True
                
                # логируем ошибки
                if flag_connection_error >= 4:
                    logger.error(
                        "ВНИМАНИЕ: Превышенно количество попыток подкючения к серверу."
                    )
                    
                else:
                    logger.warning(
                        "Программа не смогла получить ответ от радара."
                    )
                
            
            
    def process_radar_data(self, data: str):
        
        main_info_process = list()
        date_time_process = list()

        soup = BeautifulSoup(markup=data, features="html.parser")

        # получаем основную инфомрацию из сообщения и обрабатываем
        main_info = soup.find_all("div", attrs={"class": "tgme_widget_message_text"})
        
        for el in main_info:
            match = re.search(
                r"❗️Радар по всей России",
                el.text,
            )
            if not match:
                return DataAggregationService("Формат данных от радара был изменен.")
            
            # отсекаем не нужную часть, оставляем только города
            main_info_end = el.text.find("❗️")
            main_info_process.append(el.text[:main_info_end])
    
        # получаем информацию о просмтрах на сообщение и обрабатываем
        views = soup.find_all("span", attrs={"class": "tgme_widget_message_views"})
        views = [i.text for i in views]

        # получаем информацию о времени сообщения
        date_time = soup.find_all("time", attrs={"class": "time"})

        # обрабатываем данные о времени и дате. Приводим к часовому поясу Москвы.
        for t in date_time:
            dt = datetime.fromisoformat(t.get("datetime"))
            dt_shifted = dt.astimezone(timezone(timedelta(hours=3)))
            
            date_time_process.append(dt_shifted.isoformat())
        
        # все получившиеся списки склеиваем в один словарь
        processed_data = process_data(
            date_time_process,
            message_data=main_info_process,
            views_count=views,
        )
            
        # созраняем данные
        with open(DATA_FOLDER / "radar_data_proc.json", mode="w", encoding="utf-8") as f:
            json.dump(
                processed_data,
                f,
                ensure_ascii=False,
                indent=4,
            )
                
        print("process_radar_data успешно отработала.")
        
    
    def radar_is_available(self, error: bool) -> bool:
        """
        Функция безопасно делает запрос к локальному серверу.
        Обрабатывая ошибку, если сервер не работает, логирует данный факт.
        """
        try:
            requests.post("http://localhost/GetDataError", params={"error": str(error)})
            
            # если удалось оповестить сервер о потере соединения с радар, вернем true
            return True
        except RequestException:
            logger.critical(f"ВНИМАНИЕ: локальный сервер не запущен.")
            
            # если не удалось оповестить сервер, вернем false 
            return False
            
        
                       
def main():
    service = DataAggregationService()
    
    with requests.Session() as session:
        data = service.get_radar_data(session)
        service.process_radar_data(data)
        
            
        
        
        
        
main()