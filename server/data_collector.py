from requests.exceptions import RequestException
from requests import Session
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import re
from datetime import datetime, timedelta, timezone
import json
from logging.config import dictConfig
import logging
import sys
import time

# основная папка
BASE_DIR = Path(__file__).resolve().parent
print(BASE_DIR) # /home/sto-ormik/programming/python/projects/alarm/server
# тут лежат данные собранные из телеграмм канала
DATA_FOLDER = BASE_DIR / "data"

# добавляем корневую папку, чтобы не было проблем с импортом модулей из других папок
print("добавленные пути- " + str(sys.path))
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))
    
from utils import *    
    

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
        
    
    def get_radar_data(self, session: Session) -> str:
        """Данная функция очень насойчиво пытается получить данные от радара.
        Она не завершит свою работу пока их не получит.

        Args:
            session (Session): объект сессии подключения.

        Returns:
            str: основная html страница сайта радар.
        """
            
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
                if response.status_code == 200 and was_mistake:
                    
                    server_was_notified = self.local_server_notification(
                        error=False,
                        url="http://localhost/GetDataError",
                    )
                    
                # возвращает не обработанный html
                main_body = response.text
                
                with open(DATA_FOLDER / "radar_data_raw.html", mode="w", encoding="utf-8") as f:
                    f.write(main_body)
                
                logger.debug(
                    "get_radar_data успешно отработала."
                )                    
                    
                return main_body
            
            # если произошла любая ошибка, из за которй не получили новые данные
            except RequestException:
                flag_connection_error += 1
                
                # если ошибка повторяется
                if flag_connection_error >= 4 and not server_was_notified:
                    
                    # отправляем локальному серверу Flask информацию об ошибке 
                    # при этом продолжаем попытки достучаться до радара
                    server_was_notified = self.local_server_notification(
                        error=True,
                        url="http://localhost/GetDataError",
                    )
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
                    
            
            
    def process_radar_data(self, data: str, collect_data: bool = False) -> None:
        """_summary_

        Args:
            data (str): _description_

        Returns:
            DataAggregationService | None: _description_
        """
        # основные массивы для сбора информации из html
        main_info_process = list()
        date_time_process = list()

        soup = BeautifulSoup(markup=data, features="html.parser")

        # получаем основную инфомрацию из сообщения и обрабатываем
        messages = soup.find_all("div", attrs={"class": "tgme_widget_message_text"})
            
        # проходимся по всем найденным сообщениям
        for mes in messages:
            str_div = str(mes)
            
            # находим где начинается нужная часть сообщения, 
            start_id = re.search(
                r"[а-яА-яЁё]", str_div
            ).span()[0] # .span() находяться 2 значения, [0] индекс начала
            
            # находим конец нужной части
            end_id = str_div.find("<br/><br/>")
            
            # приводим контент к нужному виду
            content = re.sub(
                r"\s?<br/>\s?",
                string=str_div[start_id:end_id],
                repl=", "
            )
            
            main_info_process.append(content)
    
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
            
        # если все отработало корректно, созраняем словарь
        if isinstance(processed_data, dict):
            
            rotating_save_json(
                data=processed_data,
                f_path=DATA_FOLDER / "radar_data_proc.json",
                maxBytes=10 * 1024 * 1024,
                BackupCount=10
            )

        # если при сборе словаря произошла ошибка
        else:
            logger.critical(
                msg="ВНИМАНИЕ: данные не были сохранены."
            )
        
        logger.debug(
            "process_radar_data успешно отработала."
        )  

        
    
    def local_server_notification(self, url: str, error: bool) -> bool:
        """
        Функция безопасно делает запрос к локальному серверу.
        Обрабатывая ошибку, если сервер не работает, логирует данный факт.
        """
        try:
            requests.post(url, params={"error": str(error)})
            
            # если удалось оповестить сервер о потере соединения с радар, вернем true
            return True
        except RequestException:
            logger.critical(f"ВНИМАНИЕ: локальный сервер не запущен.")
            
            # если не удалось оповестить сервер, вернем false 
            return False
    
            
        
                       
def main():
    service = DataAggregationService()

    # создаем сессию подключения
    with requests.Session() as session:

        # получаем данные от радара
        data = service.get_radar_data(session)

        # обрабатываем данные и сохраняем их
        service.process_radar_data(data)

        # ждем 1 минуту перед следующем запросом
        time.sleep(60)

main()