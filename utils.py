import time
import subprocess
import asyncio


def process_data(keys: list, **kwargs) -> dict:
    """Обрабатывает клуючи и значения (не ограчниенное количество),
    создавая необходимую структуру словаря.

    Args:
        keys (list): Это ключи для окончательного словаря.

    Returns:
        dict: Обработанный и корректно собранынй словарь. Типа 
        {keys: {key: value, key: value, ...}}
    """

    
    values_len = len(list(kwargs.values())[0])
    if values_len != len(keys):
        raise "Количество ключей и значений не соответствует."
    
    dict_list_values = [dict() for _ in range(values_len)]
    result = dict()
    
    # проходим по ключам и спискам значений
    for key, values in kwargs.items():
        if len(values) != values_len:
            raise "Разное количество значений"
            
        # создаем список из словарей для добавления в основной словарь как значения к датам
        for id, val in enumerate(values, start=0):
            dict_list_values[id][key] = val
    
    # создаем окончательный словарик
    for time, values in zip(keys, dict_list_values):
        result[time] = values
    
    return result

    
    