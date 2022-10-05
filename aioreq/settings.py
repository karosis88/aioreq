import logging

LOGGER_NAME = 'aioreq'
MAIN_LOGGER_LEVEL = logging.DEBUG
STREAM_HANDLER_LEVEL = logging.DEBUG
FORMAT = '%(levelname)s | %(message)s | %(asctime)s'

main_logger = logging.getLogger(LOGGER_NAME)
main_logger.setLevel(MAIN_LOGGER_LEVEL)

handler = logging.StreamHandler()
handler.setLevel(STREAM_HANDLER_LEVEL)

formatter = logging.Formatter(FORMAT)

handler.setFormatter(formatter)
main_logger.addHandler(handler)
