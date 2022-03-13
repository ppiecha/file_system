import logging


def get_console_logger(name: str, log_level: int = logging.DEBUG) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level=log_level)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level=log_level)
    console_format = logging.Formatter("%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    return logger
