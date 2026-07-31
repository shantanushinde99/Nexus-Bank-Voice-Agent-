import logging
import sys

# Configure standard logger
logger = logging.getLogger("voice_banking")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")
handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(handler)


def get_logger(name: str = "voice_banking"):
    return logging.getLogger(name)
