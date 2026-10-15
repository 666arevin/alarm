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
# тут лежат данные собранные из телеграмм канала
DATA_FOLDER = BASE_DIR / "data"

# добавляем корневую папку, чтобы не было проблем с импортом модулей из других папок
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))
    
from utils import * 
from alarm_exception import *
    

# настраивавем логгер
with open(DATA_FOLDER / "log_settings.jsonc", mode="r", encoding="utf-8") as f:
    LOGGER_CONFIG = json.load(f)
    
# добавляем путь для сохранения логов
LOGGER_CONFIG["handlers"]["file"]["filename"] = str(DATA_FOLDER / "app.log")

# запускаем логгер    
dictConfig(LOGGER_CONFIG)
logger = logging.getLogger()



class FormatDataError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class DataAggregationService():
    def __init__(self):

        self.was_mistake = False

        self.was_server_notified = False
        
    
    def get_radar_data(self, session: Session, try_count: int) -> str:
        """Данная функция очень насойчиво пытается получить данные от радара.
        Она не завершит свою работу пока их не получит.

        Args:
            session (Session): объект сессии подключения.

        Returns:
            str: основная html страница сайта радар.
        """
        try:
            # получаем основные данные
            response = session.get("https://t.me/s/radarrussiia", timeout=6)

            if response.status_code == 200: 
                # возвращает не обработанный html
                main_body = response.text    

                with open(DATA_FOLDER / "radar_data_raw.html", mode="w", encoding="utf-8") as f:
                    f.write(main_body)

                return main_body
        
        # если произошла любая ошибка, из за которой не получили новые данные
        except RequestException:
                        
            # если ошибок стало 4 и более
            if try_count >= 4:
                raise RadarErrorGetDataMaxRetriers
                
            elif try_count < 4:
                raise RadarErrorGetData

            

    def fetch_with_retries(self, session: Session):

        attempt = 0
        # запускаем цикл, который не закончиться пока не получим данные от радара
        while True:
            attempt +=1
            try:
                # получаем данные от радара
                data = self.get_radar_data(
                    session=session,
                    try_count=attempt,
                )

                # оповещаем что подключение восстановленно
                if self.was_mistake:
                    self.was_server_notified = self.local_server_notification(
                        data=False,
                        url="http://localhost:9678/alarm/v1/GetDataError",
                    )

                    # если удалось оповестить сервер
                    if self.was_server_notified:
                        self.was_mistake = False

                    # если не удалось оповестить сервер
                    else:
                        logger.critical(
                            msg="ВНИМАНИЕ: локальный сервер не запущен. Доступ к радар восстановлен."
                        )

                # логируем если все успешно
                logger.debug(
                    msg="get_radar_data успешно отработала."
                )    

                return data

            except RadarErrorGetData:
                logger.warning(
                    msg=f"Не получилось получить данные от радара. Попытка -> {attempt}"
                )

            except RadarErrorGetDataMaxRetriers:

                # логируем 4 попытку
                if attempt % 10 == 0 or attempt == 4:
                    
                    logger.critical(
                        msg=f"ВНИМАНИЕ: Превышенно количество попыток подкючения к серверу. Попытка -> {attempt}"
                    )

                # если сервер еще не оповещен об ошибке
                if not self.was_server_notified:

                    self.was_server_notified = self.local_server_notification(
                        data=True,
                        url="http://localhost:9678/alarm/v1/GetDataError",
                    )

                    # если мы сервер знает об ошибке, меняем флаг
                    if self.was_server_notified:
                        self.was_mistake = True

                    # если не удалось оповестить сервер
                    else:
                        logger.critical(
                            msg="ВНИМАНИЕ: локальный сервер не запущен. Нет доступа к радар."
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
        messages = soup.find_all("div", attrs={"class": "tgme_widget_message_text js-message_text"})
            
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
            
        # если все отработало корректно, сохраняем словарь
        if isinstance(processed_data, dict):
            
            newest_message_time = rotating_save_json(
                data=processed_data,
                f_path=DATA_FOLDER / "radar_data_proc.json",
                maxBytes=10 * 1024 * 1024,
                BackupCount=10
            )

            # отправляем на сервер время последнего сообщения
            successfully = self.local_server_notification(
                data=newest_message_time,
                url="http://localhost:9678/alarm/v1/NewData",
            )
            if not successfully:
                logger.critical(
                    msg="Произошла ошибка при отправке времени последнего сообщения."
                )

        # если при сборе словаря произошла ошибка
        else:
            logger.critical(
                msg="ВНИМАНИЕ: данные не были сохранены."
            )
        
        logger.debug(
            "process_radar_data успешно отработала."
        )  

        
    
    def local_server_notification(self, url: str, data: bool | str) -> bool:
        """
        Функция безопасно делает запрос к локальному серверу.
        Обрабатывая ошибку, если сервер не работает, логирует данный факт.
        """
        try:
            requests.post(url, params={"data": str(data)})
            
            # если удалось оповестить сервер о потере соединения с радар, вернем true
            return True
        except RequestException:
            
            # если не удалось оповестить сервер, вернем false 
            return False
    
            
        
                       
def main():
    service = DataAggregationService()

    while True:
        # создаем сессию подключения
        with requests.Session() as session:

            data = service.fetch_with_retries(session=session)


            # обрабатываем данные и сохраняем их
            service.process_radar_data(data)

            # ждем 1 минуту перед следующем запросом
            time.sleep(60)

main()