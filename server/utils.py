import logging
from typing import Literal
import sys
from os import path
import os
from pathlib import Path
import json
import re
from datetime import datetime, timedelta

# логгер
logger = logging.getLogger()


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
) -> None:
    """Функция умеет записывать данные в json файл с функцией ротации.
    Если размер файла привысит maxBytes создасться новый файл а старые данные 
    уйдут в архив но будут доступна.

    Args:
        data (dict): данные которые нужно сохранить в json файл
        f_path (str | Path): файл в который нужно сохранить данные
        maxBytes (int, optional): максимальный размер файла в байтах, после ротация. Defaults to None.
        BackupCount (int, optional): количество резервных копий, после удаление. Defaults to None.
    """
    # текущие время
    current_time = datetime.now().astimezone()
    
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
        
        # делаем отдельный список с ключами 
        mes_time_list = list(radar_data.keys()).copy()
        
        for key in mes_time_list:
            time = datetime.fromisoformat(key)
           
            # если сообщение позже 15 минут
            if current_time - timedelta(minutes=15) > time:
                radar_data.pop(key)
        
        # сохраняе очищенный словарик
        with open(f_path, mode="w", encoding="utf-8") as f:
            json.dump(radar_data, f, indent=4, ensure_ascii=False)
               
        
    # после всех проверок объединяем страые данные с новыми и сохраняем в файл
    with open(f_path, mode="r", encoding="utf-8") as f:
        loaded_data = json.load(f)
    
    # обьединяем 
    for key, value in data.items():
        loaded_data[key] = value
    
    # сохраняем
    with open(f_path, mode="w", encoding="utf-8") as f:
        json.dump(loaded_data, f, ensure_ascii=False, indent=4)
        
    logger.info(
        f"функция rotating_save_json: Данные успешно сохранены в файл {f_path}."
    )
        
            
# rotating_save_json(
#     {"test": "data"},
#     "/home/sto-ormik/programming/python/projects/alarm/server/data/radar_data_proc.json",
#     BackupCount=5,
#     maxBytes=1 # 5 mb
# )

    

