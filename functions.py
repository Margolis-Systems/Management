from datetime import datetime


def ts(mode=""):
    if not mode:
        return datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    elif mode == "file_name":
        return datetime.now().strftime('%d-%m-%Y_%H-%M-%S-%f')
