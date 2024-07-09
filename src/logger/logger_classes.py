import logging
import os
import datetime
import traceback

# Define los formatters
class InfoFormatter(logging.Formatter):
    def format(self, record):
        now = datetime.datetime.now()
        formatted_date = now.strftime("%d/%m/%y %H:%M:%S")
        caller_info = self.get_caller_info(record)
        
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
    def format(self, record):
        now = datetime.datetime.now()
        formatted_date = now.strftime("%d/%m/%y %H:%M:%S")
        caller_info = self.get_caller_info(record)
        
        log_message = f"""
--------------------------------------------------------------------------------
[ {record.levelname} ]
--------------------------------------------------------------------------------

Date: {formatted_date}
Caller: {caller_info}
File: {record.pathname}
Line: {record.lineno}
PID: {os.getpid()}

Message:
{record.getMessage()}

"""

        # Agregar traceback si existe
        if record.exc_info:
            exc_lines = traceback.format_exception(*record.exc_info)
            traceback_message = "\nTraceback (most recent call last):\n" + "".join(exc_lines)
            log_message += f"Traceback:\n{traceback_message}\n"

        log_message += "--------------------------------------------------------------------------------\n"
        
        return log_message.strip()

    def get_caller_info(self, record):
        if record.funcName == "<module>":
            return f"Module: {record.module}"
        elif record.module is not None:
            return f"Class: {record.module}.{record.funcName}"
        else:
            return f"Function: {record.funcName}"

class InfoFilter(logging.Filter):
    def filter(self, record):
        return record.levelno in (logging.DEBUG, logging.INFO)

class ErrorFilter(logging.Filter):
    def filter(self, record):
        return record.levelno in (logging.ERROR, logging.WARNING, logging.CRITICAL)

class LazyFileHandler(logging.FileHandler):
    def __init__(self, filename, mode='a', encoding='utf-8', delay=True):
        self.filename = filename
        self.mode = mode
        self.encoding = encoding
        self.delay = delay
        self.stream = None  # Este atributo maneja el archivo abierto
        super().__init__(self.filename, mode=self.mode, encoding=self.encoding, delay=self.delay)

    def emit(self, record):
        """
        Emita un registro.

        Cierre y abra el archivo de nuevo si es necesario.
        """
        if self.stream is None:
            self.stream = self._open()
        super().emit(record)

    def _open(self):
        """
        Abrir el archivo de registro.
        """
        if self.encoding is None:
            stream = open(self.baseFilename, self.mode)
        else:
            stream = open(self.baseFilename, self.mode, encoding=self.encoding)
        return stream

    def close(self):
        """
        Cierre el archivo de registro si está abierto.
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        super().close()