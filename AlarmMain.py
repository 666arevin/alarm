import subprocess
import json
from pathlib import Path
import asyncio
from asyncio.exceptions import TimeoutError
import requests
from requests.exceptions import ConnectionError
from aioconsole import ainput

BASE_DIR = Path(__file__).resolve().parent
JSON_DIR = BASE_DIR / "data.json"


class AlarmManager():

    def __init__(self):


        self.alarm_notifier = AlarmNotifier()
        
    def get_radar_data(self):
        
        flag_connection_error = 0
        data = None
        while data == None:
            try:
                data = requests.request("get", "https://t.me/s/radarrussiia", timeout=5)
                data = data.json()
                with open(JSON_DIR, mode="w", encoding="utf-8") as f:
                    json.dump(data, f)
                    
                return 0

            except ConnectionError:
                print("Не удалось подклчюиться к радару.")
                flag_connection_error += 1
                
                if flag_connection_error == 4:
                    asyncio.run(
                        self.alarm_notifier.alarm_active()
                    )
                    # надо вызвать вибрацию и сигнализацию
    
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
        

    
obj = AlarmNotifier()
obj2 = AlarmManager()


res = obj2.get_radar_data()

# asyncio.run(obj.alarm_active())






