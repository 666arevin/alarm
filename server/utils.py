import logging
from typing import Literal

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

