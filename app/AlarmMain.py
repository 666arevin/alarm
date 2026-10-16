import subprocess
import time
from pathlib import Path
import asyncio
from asyncio.exceptions import TimeoutError
import requests
from requests import Session, RequestException
from aioconsole import ainput
from bs4 import BeautifulSoup
from utils import process_data
from datetime import timedelta, datetime
import re
from re import Pattern

# основная папка
BASE_DIR = Path(__file__).resolve().parent
RADAR_DATA_PATH = BASE_DIR / "radar_data"


class AlarmManager():

    def __init__(self):
        self.message_error_radar = "Не удалось подключиться к радару. Проверьте подключение к интернету."
        self.meassage_error_format = "В канале изменился формат сообщений, может привести к неправильной работе."

        self.alarm_notifier = AlarmNotifier()

    def get_processed_data(self, last_message_time: str, session: Session, try_count: int = None):

        # try:
        # получаем основные данные
        response = session.post(
            url="http://127.0.0.1:9678/alarm/v1/Products",
            params={"last_message": last_message_time},
            timeout=(3.05, 27),
        )

        if response.status_code == 200: 
            # возвращает словарик
            data = response.json()

            print(data)

            return data
        
        # если произошла любая ошибка, из за которой не получили новые данные
        # except RequestException:
                        
        #     # если ошибок стало 4 и более
        #     if try_count >= 4:
        #         raise RadarErrorGetDataMaxRetriers
                
        #     elif try_count < 4:
        #         raise RadarErrorGetData

                    
    def patter_search(self, data: dict, pattern: str | Pattern[str] = None):

        re_expression = re.compile(r"\bжуковский\b", re.IGNORECASE)

        is_matched = any(
            re.search(re_expression, message.get("message_data"))
            for message in data.values()
        )


        return is_matched

        


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
    
    async def alarm_active(self) -> int:
        """Функция запускает систему оповещения, также выодит возможность для отмены.
        

        Returns:
            int: 0 - полное отключение программы, 
                 1 - отключение сигнализации но продолжение наблюдения
        """
        
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
        

    
async def main():
    manager = AlarmManager()

    alarm = AlarmNotifier()

    last_message_time = datetime.now().astimezone() - timedelta(minutes=15)

    while True:
        with requests.Session() as session:
            try:
                # получаем данные
                data = manager.get_processed_data(
                    last_message_time,
                    session,
                )

                data["2026-10-16T23:10:52+03:00"] = {
                    "message_data": "жуковский"
                }

                if data.values():
                    last_message_time = max(
                        m.get("message_data") for m in data.values()
                    )

                is_matched =  manager.patter_search(data)

                print("Отработало")

                if is_matched:
                    await alarm.alarm_active()

            except RequestException:
                await alarm.alarm_active()

        time.sleep(60)

asyncio.run(main())






