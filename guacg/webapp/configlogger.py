import logging
import os
import time


file_path = os.path.join(os.path.abspath( os.path.dirname(__name__)), 'log')


def singleton(cls):
    instances = {}

    def _singleton(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances [cls]
    return _singleton


@singleton
class Logger():

    def __init__(self):

        if not os.path.exists(file_path):
            os.makedirs(file_path)

        file_name = 'UiBot'+time.strftime('%Y-%m-%d',time.gmtime())+'.log'
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s-%(name)s-%(funcName)s-%(levelname)s - %(message)s')
        fh = logging.FileHandler(os.path.join(file_path,file_name))
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)


loger = Logger().logger
