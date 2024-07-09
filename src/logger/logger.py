import logging
import os
from src.logger.logger_classes import *

class Logger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.logger_name = name
        
        # Limpiar handlers existentes para evitar duplicados
        self.logger.handlers = []
        
        self.create_logger_path()
        self.create_file_handlers()
        self.create_console_handlers()

    def create_logger_path(self):
        # Crear directorio para archivos de log
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_filename = f"{self.logger_name}.log"
        self.log_path = os.path.join(log_dir, log_filename)
        
    def create_file_handlers(self):
        # NOTA IMPORTANTE:
        # Con agregar estos dos handlers alcanza para todos los fines
        # Si agrego mas empiezo a tener mensajes repetidos.
        # Deberia investigar porque pasa esto.
        
        # Handlers para diferentes niveles de log
        debug_handler = LazyFileHandler(self.log_path)
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(InfoFormatter())
        debug_handler.addFilter(InfoFilter())
        self.logger.addHandler(debug_handler)
        
        warning_handler = LazyFileHandler(self.log_path)
        warning_handler.setLevel(logging.WARNING)
        warning_handler.setFormatter(ErrorFormatter())
        warning_handler.addFilter(ErrorFilter())
        self.logger.addHandler(warning_handler)
        
    def create_console_handlers(self):
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(InfoFormatter())
        self.logger.addHandler(console_handler)
        
    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message, exc_info=True)

    def error(self, message):
        self.logger.error(message, exc_info=True)

    def critical(self, message):
        self.logger.critical(message, exc_info=True)

    def get_logger(self):
        return self.logger

# Ejemplo de uso
if __name__ == "__main__":
    logger1 = Logger(__file__)
    logger1.info("Este es un mensaje informativo.")
    logger1.error("Este es un mensaje de error.")

    logger2 = Logger('otro_modulo')
    logger2.error("Este es un mensaje de error.")
