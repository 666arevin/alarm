import logging
from typing import Literal
from os import path
import time
from pathlib import Path
import json
import re
from datetime import datetime, timedelta

# логгер
logger = logging.getLogger()

class TooManyRetriersOpenFile(Exception):
    pass

def json_upload_safely(file: str | Path, data: dict) -> None:

    """Функция безопасной записи и сохранения данных в json файл.
       Функция сначала запишет данные в temp файл, а потом переименует его в основной файл.

    Args:
        file (str | Path): Файл в который нужно сохранить данные.
        data (dict): Данные которые нужно сохранить в json файл.

    Returns:
        None: _description_
    """
    # путь к временному файлу
    temp_file = Path(file).parent / "temp"

    # сохраняем данные в временный файл
    with open(temp_file, mode="w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    # переименовываем временный файл в основной
    temp_file.rename(file)

def process_data(keys: list, **kwargs) -> dict | Literal[1]:
    """Обрабатывает клуючи и значения (не ограчниенное количество),
    создавая необходимую структуру словаря.

    Args:
        keys (list): Это ключи для окончательного словаря.

    Returns:
        dict | Literal[1]: Обработанный и корректно собранынй словарь. Типа 
        {keys: {key: value, key: value, ...}}
        если при обработки данных произошла ошибка вернет 1.
    """

    # определаем длинну значений и создаем под нее список из словарей
    values_len = len(list(kwargs.values())[0])
    
    dict_list_values = [dict() for _ in range(values_len)]
    result = dict()
    
    # проходим по ключам и спискам значений
    for key, values in kwargs.items():
        
        if len(keys) != len(values):
            msg = "ВНИМАНИЕ: дальнешая обработка данных невозможна. Количество ключей и значений разное."
            logger.critical(
                msg=msg
            )
            return 1
            
        # создаем список из словарей для добавления в основной словарь как значения к датам
        for id, val in enumerate(values, start=0):
            dict_list_values[id][key] = val
    
    # создаем окончательный словарик
    for time, values in zip(keys, dict_list_values):
        result[time] = values
    
    return result

def rotating_save_json(
    data: dict, 
    f_path: str | Path,
    maxBytes: int = None, 
    BackupCount: int = None, 
) -> str:
    
    """Функция умеет записывать данные в json файл с функцией ротации.
    Если размер файла привысит maxBytes создасться новый файл а старые данные 
    уйдут в архив но будут доступна.

    Args:
        data (dict): данные которые нужно сохранить в json файл
        f_path (str | Path): файл в который нужно сохранить данные
        maxBytes (int, optional): максимальный размер файла в байтах, после ротация. Defaults to None.
        BackupCount (int, optional): количество резервных копий, после удаление. Defaults to None.
    
    Return:
        str: возвразает время строкой в формате iso для последнего сообщения.
    """
    # текущие время в формате iso
    current_time = datetime.now().astimezone()
    last_1hour = (current_time - timedelta(minutes=60)).isoformat()
    
    # проверяем что файл существует, создаем его если нужно
    f_path = Path(f_path)
    if not path.exists(f_path):
        
        with open(f_path, mode="w", encoding="utf-8") as f:
            json.dump({}, f)

    # если задан макс размер файла и размер файла больше заданного, делаем ротацию
    if maxBytes and path.getsize(f_path) > maxBytes:
        
        # список всех backup файлов
        escaped_file = re.escape(f_path.name)
        files = sorted([
            f for f in f_path.parent.iterdir()
            if re.match(rf"{escaped_file}\.\d*", f.name)
        ], reverse=True)
                
        for f in files:
            f_id = int(f.name.split(".")[-1])

            # проверяем задан ли параметр BackupCount
            if BackupCount and int(f_id) < BackupCount:
                f.rename(f_path.parent / f"{f_path.name}.{f_id + 1}")

            # если не задан просто переименовываем
            elif not BackupCount:
                f.rename(f_path.parent / f"{f_path.name}.{f_id + 1}")

            # если файл превыщает количество бэкапов, удаляем его
            else:
                f.unlink()

        # текущий файл копируем в архив, после убираем из него все старые сообщения
        f_path.copy(f_path.parent / f"{f_path.name}.1")
        
        with open(f_path, mode="r", encoding="utf-8") as f:
            radar_data: dict = json.load(f)
        

        # собираем только отфильтрованные данные (сообщения за последние 30 минут)
        filtered_radar_data = {
            key: value 
            for key, value in radar_data.items()
            if key >= last_1hour
        }
        
        # сохраняем отфильтрованный словарик
        json_upload_safely(data=filtered_radar_data, file=f_path)
               
        
    # после всех проверок объединяем страые данные с новыми и сохраняем в файл
    with open(f_path, mode="r", encoding="utf-8") as f:
        loaded_data = json.load(f)
    
    # обьединяем 
    loaded_data |= data
    newest_message_time = max(loaded_data)

    # сохраняем
    json_upload_safely(data=loaded_data, file=f_path)

    logger.info(
        f"функция rotating_save_json: Данные успешно сохранены в файл {f_path}."
    )

    return newest_message_time
        

def str_to_bool(s: str) -> bool:
    """Преобразует строку в булево значение.

    Args:
        s (str): строка для преобразования

    Returns:
        bool: True или False
    """
    return s.lower() == "true"


# rotating_save_json(
#     {"test": "data"},
#     "/home/sto-ormik/programming/python/projects/alarm/server/data/radar_data_proc.json",
#     BackupCount=5,
#     maxBytes=1 # 5 mb
# )

    

