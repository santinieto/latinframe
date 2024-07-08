import logging
import datetime
import os
from tkinter import Text, END

class InfoFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()
        # Instancia un logger que apunte al mismo logger que la clase Logger
        self.logger = Logger().get_logger()

    def format(self, record):
        # Obtener la fecha y hora actual
        now = datetime.datetime.now()
        formatted_date = now.strftime("%d/%m/%y %H:%M:%S")
        caller_info = self.get_caller_info(record)
        
        # Construir el mensaje de registro
        log_message = f"""
================================================================================
[ {record.levelname} ] - {caller_info} - {formatted_date}
--------------------------------------------------------------------------------
{record.msg}
--------------------------------------------------------------------------------
"""
        return log_message.strip()

    def get_caller_info(self, record):
        if record.funcName == "<module>":
            return f"Module: {record.module}"
        elif record.module is not None:
            return f"Class: {record.module}.{record.funcName}"
        else:
            return f"Function: {record.funcName}"
    
class ErrorFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()
        # Instancia un logger que apunte al mismo logger que la clase Logger
        self.logger = Logger().get_logger()

    def format(self, record):
        # Obtener la fecha y hora actual
        now = datetime.datetime.now()
        formatted_date = now.strftime("%d/%m/%y %H:%M:%S")
        caller_info = self.get_caller_info(record)
        
        # Construir el mensaje de registro
        log_message = f"""
        --------------------------------------------------------------------------------
        [ {record.levelname} ]
        --------------------------------------------------------------------------------

        Date: {formatted_date}
        Caller: {caller_info}
        File: {record.filename}
        Line: {record.lineno}
        PID: {os.getpid()}

        Message:
        {record.msg}

        --------------------------------------------------------------------------------
        """
        return log_message.strip()

    def get_caller_info(self, record):
        if record.funcName == "<module>":
            return f"Module: {record.module}"
        elif record.module is not None:
            return f"Class: {record.module}.{record.funcName}"
        else:
            return f"Function: {record.funcName}"

class Logger:
    _instance = None

    def __new__(cls,
                info_file = 'info.log',
                debug_file = 'debug.log',
                warning_file = 'warning.log',
                error_file = 'errors.log',
                reset_files = True
                ):
        """
        Crea una instancia única del logger utilizando el patrón Singleton.

        :param info_file: Nombre de archivo para mensajes INFO.
        :param debug_file: Nombre de archivo para mensajes DEBUG.
        :param warning_file: Nombre de archivo para mensajes WARNING.
        :param error_file: Nombre de archivo para mensajes ERROR.
        :param reset_files: Booleano para reiniciar archivos de log existentes.
        :return: Instancia única del logger.
        """
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialize_logger(info_file, debug_file, warning_file, error_file, reset_files)
        return cls._instance

    def _initialize_logger(self, info_file, debug_file, warning_file, error_file, reset_files):
        """
        Inicializa el logger con diferentes manejadores y formateadores.

        :param info_file: Nombre de archivo para mensajes INFO.
        :param debug_file: Nombre de archivo para mensajes DEBUG.
        :param warning_file: Nombre de archivo para mensajes WARNING.
        :param error_file: Nombre de archivo para mensajes ERROR.
        :param reset_files: Booleano para reiniciar archivos de log existentes.
        """
        # Configura el objeto Logger con la codificación UTF-8
        logging.basicConfig(encoding='utf-8')
        
        # Desactivar los manejadores del logger raíz
        # Ejecutar esto siempre DESPUES del basicConfig()
        logging.root.handlers = []
        
        # Obtngo una instancia del logger
        self.logger = logging.getLogger('Logger')
        
        # Establece el nivel de registro del logger
        self.logger.setLevel(logging.DEBUG)

        # Verificar si el manejador de archivo ya está presente antes de agregarlo
        existing_handlers = [handler for handler in self.logger.handlers if isinstance(handler, logging.FileHandler)]

        # Crear manejador de consola
        if not any(isinstance(handler, logging.StreamHandler) for handler in self.logger.handlers):
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(InfoFormatter())
            self.logger.addHandler(console_handler)

        # Crear directorio para archivos de log
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_mode = 'w' if reset_files else 'a'

        # Crear manejadores de archivo
        if not any(handler.baseFilename == os.path.join(log_dir, info_file) for handler in existing_handlers):
            info_file_handler = logging.FileHandler(os.path.join(log_dir, info_file), mode=file_mode, encoding='utf-8')
            info_file_handler.setLevel(logging.INFO)
            info_file_handler.setFormatter(InfoFormatter())
            self.logger.addHandler(info_file_handler)

        if not any(handler.baseFilename == os.path.join(log_dir, debug_file) for handler in existing_handlers):
            debug_file_handler = logging.FileHandler(os.path.join(log_dir, debug_file), mode=file_mode, encoding='utf-8')
            debug_file_handler.setLevel(logging.DEBUG)
            debug_file_handler.setFormatter(InfoFormatter())
            self.logger.addHandler(debug_file_handler)

        if not any(handler.baseFilename == os.path.join(log_dir, warning_file) for handler in existing_handlers):
            warning_file_handler = logging.FileHandler(os.path.join(log_dir, warning_file), mode=file_mode, encoding='utf-8')
            warning_file_handler.setLevel(logging.WARNING)
            warning_file_handler.setFormatter(ErrorFormatter())
            self.logger.addHandler(warning_file_handler)

        if not any(handler.baseFilename == os.path.join(log_dir, error_file) for handler in existing_handlers):
            error_file_handler = logging.FileHandler(os.path.join(log_dir, error_file), mode=file_mode, encoding='utf-8')
            error_file_handler.setLevel(logging.ERROR)
            error_file_handler.setFormatter(ErrorFormatter())
            self.logger.addHandler(error_file_handler)

    def get_logger(self):
        """
        Obtiene la instancia del logger.

        :return: Instancia del logger.
        """
        return self.logger

    def add_log_level(self, level_name, level_num):
        """
        Añade un nuevo nivel de logeo al logger.

        :param level_name: Nombre del nuevo nivel de logeo.
        :param level_num: Valor numérico del nuevo nivel de logeo.
        """
        logging.addLevelName(level_num, level_name.upper())

        def log_for_level(self, message, *args, **kwargs):
            if self.isEnabledFor(level_num):
                self._log(level_num, message, args, **kwargs)

        setattr(logging.getLoggerClass(), level_name.lower(), log_for_level)

        file_handler = logging.FileHandler(os.path.join('logs', f'{level_name.lower()}.log'), encoding='utf-8')
        file_handler.setLevel(level_num)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
        self.logger.addHandler(file_handler)
        
# Uso del logger
if __name__ == '__main__':
    logger = Logger(info_file='my_info.log', reset_files=True).get_logger()
    logger.info('Este es un mensaje informativo')
    logger.debug('Este es un mensaje de debug')
    logger.warning('Este es un mensaje de advertencia')
    logger.error('Este es un mensaje de error')

    # Añadir un nuevo nivel de logeo
    logger_singleton = Logger()
    logger_singleton.add_log_level('unittest', 25)
    logger = logger_singleton.get_logger()
    logger.unittest('Este es un mensaje de unittest')
