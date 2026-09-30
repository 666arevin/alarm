import subprocess
import json
from pathlib import Path
import asyncio
from asyncio.exceptions import TimeoutError
import requests
from requests.exceptions import ConnectionError, ReadTimeout
from aioconsole import ainput
from bs4 import BeautifulSoup
from utils import process_data
from datetime import *
import re

BASE_DIR = Path(__file__).resolve().parent
RADAR_DATA_PATH = BASE_DIR / "radar_data"


class AlarmManager():

    def __init__(self):
        self.message_error_radar = "Не удалось подключиться к радару. Проверьте подключение к интернету."
        self.meassage_error_format = "В канале изменился формат сообщений, может привести к неправильной работе."

        self.alarm_notifier = AlarmNotifier()
        
    def get_radar_data(self):
        
        flag_connection_error = 0
        data = None
        
        while data == None:
            try:
                data = requests.request("get", "https://t.me/s/radarrussiia", timeout=5)
                with open(RADAR_DATA_PATH / "radar.html", mode="w", encoding="utf-8") as f:
                    f.write(data.text)
                    
                return 0

            except ConnectionError, ReadTimeout:
                print("Не удалось подключиться к радару.")
                flag_connection_error += 1
                
                # если ошибка повторяется, вызываем тревогу
                if flag_connection_error == 4:
                    asyncio.run(
                        self.alarm_notifier.alarm_active(
                            mes=self.message_error_radar
                        )
                    )
                    
    
    def process_radar_data(self):   
        main_info_process = list()
        date_time_process = list()

        # открываем файл с html страницой
        with open(RADAR_DATA_PATH / "radar.html", mode="r", encoding="utf-8") as f:
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
                asyncio.run(
                    self.alarm_notifier.alarm_active(
                        mes=self.meassage_error_formatб
                    )
                )
            
            main_info_end = el.text.find("❗️")
            print(el.text[:main_info_end] + " | " + str(main_info_end))
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
            
        processed_data = process_data(
            date_time_process,
            message_data=main_info_process,
            views_count=views,
        )
            
        # Собираем окончательный словарь
        print(processed_data)
        with open(RADAR_DATA_PATH / "radar_data_proc.json", mode="w", encoding="utf-8") as f:
            json.dump(
                processed_data,
                f,
                ensure_ascii=False,
                indent=4,
            )
    
    def pattern_search(self):
        pass


class AlarmNotifier():

    def __init__(self):
        pass


    async def alarm(self, debug: bool = False):
        # включаем оповещение
        print("Сигнализация активна.")
        try:
            subprocess.run(["termux-media-player", "play", "~/downloads/c0741610c2c6cfc.mp3"])
        except FileNotFoundError:
            if debug == True:
                print("Не могу включить сигнализацию на этом устройстве.")
        
        print("Вибрация активна.")
        # 24
        for _ in range(24):
            await asyncio.sleep(0.8)
            try:
                subprocess.run(["termux-vibrate", "-d", "500", "-f"])
            except FileNotFoundError:
                if debug == True:
                    print("Не могу вибирировать на этом устройстве.")


    async def alarm_deactiv(self):

        text1 = "Для полной остановки введите: STOP"
        text2 = "Продолжить наблюдене но отключить сигнализацию: RESUME"
        print(text1 + "\n" + text2)

        # ждем пока пользователь введет остановку сигнализации
        try:
            user_text = await asyncio.wait_for(
                    ainput(),
                    timeout=31
                )
            
        except TimeoutError:
            return 1
        
        return user_text
    
    async def alarm_active(self, mes: str) -> int:
        """Функция запускает систему оповещения, также выодит возможность для отмены.
        

        Returns:
            int: 0 - полное отключение программы, 
                 1 - отключение сигнализации но продолжение наблюдения
        """
        print(mes)
        
        task1 = asyncio.create_task(self.alarm())
        task2 = asyncio.create_task(self.alarm_deactiv())
    
        
        # данный цикл будет давать ввод для пользовтеля, пока он не отменит
        # сигнализацию, или она не завершиться по времени.
        while True:
            user_text = await task2
            
            if user_text == 1:
                print("Сигнализация завершена по времени.")
                return 1
                
            elif user_text.lower() == "stop":
                task1.cancel()
                print("Сигнализация успешно отменена. Наблюдение отменено.")
                return 0
            
            elif user_text.lower() == "resume":
                print("Сигнализация успешно отменена. Наблюдение продолжаю.")
                return 1
            
            else:   
                task2 = asyncio.create_task(self.alarm_deactiv())
        

    
obj = AlarmNotifier()
obj2 = AlarmManager()

obj2.get_radar_data()
obj2.process_radar_data()
# res = obj2.get_radar_data()

# asyncio.run(obj.alarm_active())






