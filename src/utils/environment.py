# Imports estándar de Python
import os
import json
from pathlib import Path
# import sys

# Añade el directorio raíz del proyecto a sys.path
# current_path = os.path.dirname(os.path.abspath(__file__))
# project_root = os.path.abspath(os.path.join(current_path, '..', '..'))  # Ajusta según la estructura de tu proyecto
# sys.path.append(project_root)

# Imports de terceros
# Ninguno en este set

# Imports locales
from src.logger.logger import Logger

################################################################################
# Genero una instancia del Logger
################################################################################
logger = Logger(os.path.basename(__file__)).get_logger()

# Variables globables
DEFAULT_ENVIRONMENT_VERBOSE = False

def load_json(filename='', verbose=DEFAULT_ENVIRONMENT_VERBOSE):
    """
    Carga variables de entorno desde un archivo JSON.

    Parámetros:
    filename (str): La ruta del archivo JSON que contiene las variables de entorno.
    verbose (bool): Si es True, se imprimirán mensajes informativos.
    logger (Logger): Instancia de la clase Logger para manejar los mensajes de log.

    Ejemplo de uso:
    logger = Logger()
    load_json('config.json', verbose=True, logger=logger)
    """
    try:
        # Intentar abrir y cargar el contenido del archivo JSON
        with open(filename, 'r') as archivo:
            datos_json = json.load(archivo)
            
            # Crear un diccionario con las variables de entorno a partir del JSON
            entorno = {clave: str(valor) for clave, valor in datos_json.items()}
            os.environ.update(entorno)  # Actualizar las variables de entorno
            
            # Imprimir mensajes informativos si verbose es True
            if logger and verbose:
                for clave, valor in entorno.items():
                    logger.info(f'Se ha establecido la variable de entorno [{clave}] : [{valor}]')
            if logger:
                logger.info('Variables de entorno cargadas exitosamente.')
    
    except FileNotFoundError:
        if logger:
            logger.error(f'Error: El archivo {filename} no fue encontrado.')
    except json.JSONDecodeError:
        if logger:
            logger.error(f'Error: No se pudo decodificar el contenido JSON del archivo {filename}.')
    except Exception as e:
        if logger:
            logger.error(f'Ocurrió un error inesperado: {str(e)}')

def set_environment(filename=None, verbose=DEFAULT_ENVIRONMENT_VERBOSE):
    """
    Configura las variables de entorno necesarias para la aplicación.

    Parámetros:
    logger (Logger): Instancia de la clase Logger para manejar los mensajes de log.
    """
    
    # Obtener el directorio actual
    home = Path.cwd()

    # Establecer variables de entorno
    os.environ["SOFT_HOME"] = str(home)
    os.environ["SOFT_RESULTS"] = str(home / 'results')
    os.environ["SOFT_UTILS"] = str(home / 'utils')
    os.environ["SOFT_EXCLUDED"] = str(home / 'excluded')
    os.environ["SOFT_LOGS"] = str(home / 'logs')
    os.environ["SOFT_MP_ENABLE"] = 'True'
    os.environ["SOFT_MP_NTHREADS"] = str(max(1, os.cpu_count() // 2))
    
    # Cargo el nombre del archivo si es pasado por afuera
    if filename is None:
        credentials_file_path = Path(os.environ["SOFT_UTILS"]) / 'settings.json'
    else:
        credentials_file_path = Path(filename)

    # Cargar las variables desde el archivo JSON
    load_json(filename=str(credentials_file_path))

    # Leer las credenciales desde el archivo JSON
    try:
        with open(credentials_file_path, 'r') as config_file:
            config = json.load(config_file)

        os.environ["EMAIL_ADRESS"] = config.get("EMAIL_ADRESS", '')
        os.environ["EMAIL_PASSWORD"] = config.get("EMAIL_PASSWORD", '')
        os.environ["EMAIL_PLATFORM"] = config.get("EMAIL_PLATFORM", '')

        if verbose:
            logger.info(f'Se ha establecido la variable de entorno [EMAIL_ADRESS] : [{os.environ["EMAIL_ADRESS"]}]')
            logger.info(f'Se ha establecido la variable de entorno [EMAIL_PASSWORD] : [{os.environ["EMAIL_PASSWORD"]}]')
            logger.info(f'Se ha establecido la variable de entorno [EMAIL_PLATFORM] : [{os.environ["EMAIL_PLATFORM"]}]')
            logger.info('Variables de entorno cargadas exitosamente.')
    except FileNotFoundError as e:
        os.environ["EMAIL_ADRESS"] = ''
        os.environ["EMAIL_PASSWORD"] = ''
        os.environ["EMAIL_PLATFORM"] = ''
        msg = f'El archivo de credenciales {credentials_file_path} no fue encontrado. Error: {e}'
        logger.error(msg)
    except json.JSONDecodeError as e:
        os.environ["EMAIL_ADRESS"] = ''
        os.environ["EMAIL_PASSWORD"] = ''
        os.environ["EMAIL_PLATFORM"] = ''
        msg = f'No se pudo decodificar el contenido JSON del archivo {credentials_file_path}. Error: {e}'
        logger.error(msg)
    except Exception as e:
        os.environ["EMAIL_ADRESS"] = ''
        os.environ["EMAIL_PASSWORD"] = ''
        os.environ["EMAIL_PLATFORM"] = ''
        msg = f'No se pudieron cargar las variables de entorno. Error: {e}'
        logger.error(msg)

def unset_environment(filename=None, verbose=DEFAULT_ENVIRONMENT_VERBOSE):
    """
    Elimina las variables de entorno necesarias para la aplicación.
    """
    # Elimino las variables basicas
    variables_a_eliminar = [
        "SOFT_HOME", "SOFT_RESULTS", "SOFT_UTILS", "SOFT_LOGS",
        "SOFT_MP_ENABLE", "SOFT_MP_NTHREADS",
        "EMAIL_ADRESS", "EMAIL_PASSWORD", "EMAIL_PLATFORM"
    ]
    for variable in variables_a_eliminar:
        if verbose:
            logger.info(f'Se va a borrar la variable de entorno [{variable}]')
        os.environ.pop(variable, None)

    # Si se proporciona un nombre de archivo, elimina las variables de entorno adicionales
    if filename:
        try:
            with open(filename, 'r') as archivo:
                datos_json = json.load(archivo)

                for clave in datos_json.keys():
                    if verbose:
                        logger.info(f'Se va a borrar la variable de entorno adicional [{clave}]')
                    os.environ.pop(clave, None)
        except FileNotFoundError:
            if verbose:
                logger.info(f'El archivo {filename} no fue encontrado.')
        except json.JSONDecodeError:
            if verbose:
                logger.info(f'Error al decodificar el contenido JSON del archivo {filename}.')

if __name__ == '__main__':
    set_environment()
