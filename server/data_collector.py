from requests.exceptions import RequestException
from requests import Session
import requests
from bs4 import BeautifulSoup
from pathlib import Path


# основная папка
BASE_DIR = Path(__file__).resolve().parent
# тут лежат данные собранные из телеграмм канала
DATA_FOLDER = BASE_DIR / "radar_data"


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
        data = None
        
        while data == None:
            try:
                response = session.get("https://t.me/s/radarrussiia", timeout=5)
                main_body = response.text
                # возвращает не обработанный html
                return main_body
            
            # если произошла любая ошибка, из за которй не получили новые данные
            except RequestException:
                print("Не удалось подключиться к радару.")
                flag_connection_error += 1
                
                # если ошибка повторяется, делаем активный спец флаг для сигнализации
                return ServerErrorGetData("Сервер не мог получить данный от радара.")
            
    def process_radar_data(self):   
        main_info_process = list()
        date_time_process = list()

        # открываем файл с html страницой
        with open(DATA_FOLDER / "radar.html", mode="r", encoding="utf-8") as f:
            html = f.read()
            
        soup = BeautifulSoup(markup=html, features="html.parser")

        # получаем основную инфомрацию из сообщения и обрабатываем
        main_info = soup.find_all("div", attrs={"class": "tgme_widget_message_text"})
        
        for el in main_info:
            match = re.search(
                r"❗️Радар по всей России",
                el.text,
            )
            if not match:
                return
            
            main_info_end = el.text.find("❗️")
            print(el.text[:main_info_end] + " | " + str(main_info_end))
            main_info_process.append(el.text[:main_info_end])
    
            
def main():
    service = DataAggregationService()
    
    with requests.Session() as session:
        data = service.get_radar_data(session)
        print(data)
        

main()