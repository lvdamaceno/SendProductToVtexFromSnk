import logging
import os


def configure_logging():
    env = os.getenv('APP_ENV')

    if env == '1':
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(name)s - %(filename)s:%(lineno)d - %(message)s')
    logging.debug(f"Valor da variável de ambiente APP_ENV: '{env}'")
