"""
Exercise handlers.
"""

import logging


class GracefulException(Exception):
    """
    Custom exception handler. Provides predictable and uniform logging output.
    """

    def __init__(self, message):
        Exception.__init__(self)
        logging.error(message)
        logging.fatal("Application can't continue!")
        exit(-1)
