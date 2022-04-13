import logging


def get_formatter():
    return logging.Formatter("%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s")


def get_console_handler(log_level: int = logging.DEBUG) -> logging.StreamHandler:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level=log_level)
    console_handler.setFormatter(get_formatter())
    return console_handler


def get_file_handler(log_level: int = logging.DEBUG, file_name="file_system.log") -> logging.FileHandler:
    file_handler = logging.FileHandler(file_name)
    file_handler.setLevel(level=log_level)
    file_handler.setFormatter(get_formatter())
    return file_handler


def get_console_logger(name: str, log_level: int = logging.DEBUG) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level=log_level)
    console_handler = get_console_handler(log_level=log_level)
    logger.addHandler(console_handler)
    return logger
