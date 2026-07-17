import logging
import os

LOG_DIR = "logs"

os.makedirs(LOG_DIR, exist_ok=True)


def setup_logger(name: str):

    logger = logging.getLogger(name)

    logger.setLevel(logging.INFO)

    if not logger.handlers:

        handler = logging.FileHandler(
            f"{LOG_DIR}/app.log"
        )

        formatter = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
        )

        handler.setFormatter(formatter)

        logger.addHandler(handler)

    return logger