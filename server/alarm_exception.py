class RadarErrorGetData(Exception):
    """Вызывается если радар по какой то причине не доступен.

    Args:
        Exception (_type_): _description_
    """
    

class RadarErrorGetDataMaxRetriers(Exception):
    """Вызывается, если число попыток подключения к радару
    превысило максимально допустимое.

    Args:
        Exception (_type_): _description_
    """


class LocalServerNotAvailable(Exception):
    """Ошибка, которая возникает когда при попытке оповестить
    сервер, ничего не вышло, он не доступен.

    Args:
        Exception (_type_): _description_
    """

class DifferentLenghts(Exception):
    """Ошибка возникает при сравнение длины ключей и значений.
    Если длина разная выдаст ошибку, такие ключи и значения не получиться
    склеить в словарь.

    Args:
        Exception (_type_): _description_
    """

class DataParseFailed(Exception):
    """Ошибка возникакет, когда метод find_all при попытке найти нужные
    даныне вернул пустой список.

    Args:
        Exception (_type_): _description_
    """