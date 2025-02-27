# LOGGING_FUNCTIONS

# -----------------------------------------------------------------------------
# IMPORT LIBRARIES

import inspect
import logging
import logging.handlers
import os
from queue import Queue
from typing import Optional



# -----------------------------------------------------------------------------
# LOGGER


class Logger:
    """
    A class to configure and manage asynchronous logging.
    """
    _instance: Optional['Logger'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.logger = logging.getLogger('GlobalAiLogger')

        self.logger.setLevel(logging.DEBUG)

        # Create a queue for asynchronous logging
        self.log_queue = Queue(-1)  # No size limit

        # Create handlers only if no handlers are present
        if not self.logger.handlers:
            log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

            # Define the path to the log file
            log_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'logs.log'))
            if not os.path.exists(log_file_path):
                with open(log_file_path, 'w') as f:
                    pass

            # File Handler
            file_handler = logging.FileHandler(
                filename=log_file_path,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(log_format)

            # Stream Handler (console)
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.DEBUG)
            stream_handler.setFormatter(log_format)

            # Queue Handler
            queue_handler = logging.handlers.QueueHandler(self.log_queue)
            queue_handler.setLevel(logging.DEBUG)
            queue_handler.setFormatter(log_format)

            self.logger.addHandler(queue_handler)

            # Set up Queue Listener
            self.queue_listener = logging.handlers.QueueListener(
                self.log_queue,
                file_handler,
                stream_handler,
                respect_handler_level=True
            )
            self.queue_listener.start()

    def get_logger(self) -> logging.Logger:
        """
        Retrieve the configured logger instance.

        Returns:
            logging.Logger: The logger instance.
        """
        return self.logger

    def shutdown(self):
        """
        Shutdown the queue listener gracefully.
        """
        self.queue_listener.stop()


def print_error(e: Exception) -> None:
    """
    Log and display detailed information about an error asynchronously.

    Args:
        e (Exception): The exception to log.
    """
    logger_instance = Logger().get_logger()
    frame = inspect.currentframe()
    if frame is not None:
        caller_frame = frame.f_back
        if caller_frame is not None:
            frame_info = inspect.getframeinfo(caller_frame)
            error_name = os.path.basename(frame_info.filename)
            error_line = e.__traceback__.tb_lineno if e.__traceback__ else 'Unknown'
            error_function = frame_info.function
            text = f'{error_name}, line {error_line}, in {error_function}() -- {e}'
            logger_instance.exception(text, exc_info=e)
        else:
            logger_instance.exception(f'Exception occurred: {e}', exc_info=e)
    else:
        logger_instance.exception(f'Exception occurred: {e}', exc_info=e)
