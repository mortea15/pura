import logging
import os


filename = 'pura'

logFormatter = logging.Formatter('%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s')
rootLogger = logging.getLogger()
rootLogger.setLevel(50)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)

def increase_log_level():
    levels = {
        50: 'CRITICAL',
        40: 'ERROR',
        30: 'WARNING',
        20: 'INFO',
        10: 'DEBUG'
    }
    current = rootLogger.level
    if current > 10:
        new_level = current - 10
        if new_level % 10 == 0 and new_level in range(10,51):
            rootLogger.setLevel(current - 10)
            print(f'Set log level to {levels.get(new_level)}')

def log_to_file():
    fileHandler = logging.FileHandler(f'{filename}.log')
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)