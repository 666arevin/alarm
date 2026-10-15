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