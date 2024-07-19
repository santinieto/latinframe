# Imports estándar de Python
import os
from datetime import timedelta, datetime
from pathlib import Path
import time
# import sys

# Añade el directorio raíz del proyecto a sys.path
# current_path = os.path.dirname(os.path.abspath(__file__))
# project_root = os.path.abspath(os.path.join(current_path, '..', '..'))  # Ajusta según la estructura de tu proyecto
# sys.path.append(project_root)

# Imports de terceros
from bs4 import BeautifulSoup
import requests
import re
import random
import json
import platform

# Imports locales
from src.logger.logger import Logger

################################################################################
# Genero una instancia del Logger
################################################################################
logger = Logger(os.path.basename(__file__)).get_logger()

# Variables globables
HEADER = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
SIMILARWEB_BASE_URL = 'https://www.similarweb.com/'
DEFAULT_UTILS_VERBOSE = False

def get_http_response(url, headers=None, response_type='page', verbose=DEFAULT_UTILS_VERBOSE, debug=False, timeout=10, retry_attempts=3):
    """
    Obtiene la respuesta HTML de una URL.
    Puede aceptar headers personalizados; si no se proporcionan, utiliza unos por defecto.
    La función retorna el resultado HTML como un objeto BeautifulSoup o texto plano.

    Args:
        url (str): La URL de la página web.
        headers (dict, optional): Headers para la solicitud HTTP.
        response_type (str, optional): Tipo de respuesta ('page' para BeautifulSoup, 'text' para texto plano).
        verbose (bool, optional): Si es True, imprime información detallada.
        debug (bool, optional): Si es True, imprime la respuesta HTTP completa.
        timeout (int, optional): Tiempo máximo de espera para la solicitud HTTP en segundos.
        retry_attempts (int, optional): Número de intentos de reintentos en caso de fallo.

    Returns:
        BeautifulSoup object or str: Dependiendo de response_type, retorna un objeto BeautifulSoup o texto plano.

    Raises:
        ValueError: Si response_type no es 'page' o 'text'.
        RuntimeError: Si ocurre un error durante la solicitud HTTP.
    """
    # Validación de parámetros
    if not isinstance(url, str):
        raise ValueError("La URL debe ser una cadena de caracteres.")
    if headers is not None and not isinstance(headers, dict):
        raise ValueError("Headers debe ser un diccionario.")
    if response_type not in ['page', 'text']:
        raise ValueError("response_type debe ser 'page' o 'text'.")
    if not isinstance(verbose, bool):
        raise ValueError("verbose debe ser un valor booleano.")
    if not isinstance(debug, bool):
        raise ValueError("debug debe ser un valor booleano.")
    if not isinstance(timeout, (int, float)):
        raise ValueError("timeout debe ser un número.")
    if not isinstance(retry_attempts, int) or retry_attempts < 0:
        raise ValueError("El número de intentos de reintentos debe ser un entero no negativo.")

    # Definimos los headers por defecto
    if headers is None:
        headers = {
            'user-agent': HEADER
        }

    attempts = 0
    while attempts <= retry_attempts:
        try:
            # Realizamos una solicitud a la página web con timeout
            response = requests.get(url, headers=headers, timeout=timeout)

            # Debug: Imprimimos la respuesta completa si debug es True
            if debug:
                logger.debug(f'HTTP response: {response}')

            # Analizamos el contenido HTML de la página web utilizando BeautifulSoup
            page = BeautifulSoup(response.content, 'html.parser')

            # Verbose: Imprimimos información detallada si verbose es True
            if verbose:
                msg  = f'URL [{url}], '
                msg += f'HTTP status [{response.ok}], '
                msg += f'HTTP code [{response.status_code}]'
                logger.info(msg)

            # Validación de la respuesta
            if response.ok:
                if response_type == 'text':
                    return response.text
                else:
                    return page
            else:
                msg  = f'URL [{url}], '
                msg += f'HTTP status [{response.ok}], '
                msg += f'HTTP code [{response.status_code}], '
                msg += f'Message [ERROR! Ocurrió un error inesperado al cargar la URL seleccionada]'
                logger.error(msg)
                return None

        except requests.RequestException as e:
            if verbose:
                logger.error(f'ERROR! Ocurrió un error al realizar la solicitud HTTP para la URL [{url}]. Error: [{e}]')

            # Incrementamos el contador de intentos y esperamos antes de reintentar
            attempts += 1
            if attempts <= retry_attempts:
                time.sleep(1)  # Esperamos 1 segundo antes de realizar el siguiente intento

    # Si llegamos aquí, significa que todos los intentos de reintentos fallaron
    logger.error(f"No se pudo obtener la respuesta HTTP para la URL [{url}] después de {retry_attempts} intentos.")
    return None

def get_os():
    """
    Obtiene la versión del sistema operativo que se está usando.
    
    Returns:
        str: El nombre del sistema operativo.
    
    Raises:
        RuntimeError: Si no se puede determinar el sistema operativo.
    """
    try:
        # Obtengo la versión del sistema operativo
        os_name = platform.system()
        
        # Validar que el nombre del sistema operativo no esté vacío
        if not os_name:
            raise RuntimeError("No se pudo determinar el sistema operativo.")
        
        # Devuelvo el nombre del sistema operativo
        return os_name
    except Exception as e:
        # Manejo de excepciones y generación de un mensaje de error descriptivo
        raise RuntimeError(f"Error al obtener el sistema operativo: {e}")

def clean_and_parse_number(num_str, verbose=DEFAULT_UTILS_VERBOSE):
    """
    Limpia y parsea una cadena de texto que representa un número, eliminando la puntuación y convirtiéndola en un número real.

    Args:
        num_str (str): Una cadena de texto que representa un número, potencialmente conteniendo puntuación y unidades abreviadas.

    Returns:
        float: El número real parseado extraído de la cadena de texto de entrada.
    """
    try:
        # Eliminar la puntuación de la cadena de texto
        num_limpo_str = re.sub(r'[^\d.umkKMGT]', '', num_str)
        
        # Convertir la cadena de texto limpia en un número real
        if 'u' in num_limpo_str:
            num = round(float(num_limpo_str.replace('u', '')) * 1e-6, 8)
        elif 'm' in num_limpo_str:
            num = round(float(num_limpo_str.replace('m', '')) * 1e-3, 6)
        elif 'k' in num_limpo_str or 'K' in num_limpo_str:
            num = round(float(num_limpo_str.replace('k', '').replace('K', '')) * 1e3, 2)
        elif 'M' in num_limpo_str:
            num = round(float(num_limpo_str.replace('M', '')) * 1e6, 2)
        elif 'G' in num_limpo_str:
            num = round(float(num_limpo_str.replace('G', '')) * 1e9, 2)
        elif 'T' in num_limpo_str:
            num = round(float(num_limpo_str.replace('T', '')) * 1e12, 2)
        else:
            num = round(float(num_limpo_str), 2)

        return num
    except ValueError:
        # Si ocurre un error al convertir la cadena en un número, imprimir un mensaje de error y devolver None
        if verbose:
            logger.error(f"La cadena [{num_str}] no representa un número válido y no pudo ser formateada.")
        return 0.0
    except Exception as e:
        # Si ocurre cualquier otro tipo de error, imprimir un mensaje de error con la descripción del error y devolver None
        if verbose:
            logger.error(f"Error inesperado al intentar formatear la cadena de entrada {num_str}")
        return 0.0

def str_to_bool(s):
    """
    Convierte una cadena a un valor booleano.
    
    Args:
        s (str): La cadena a convertir.
    
    Returns:
        bool: El valor booleano correspondiente.
    
    Raises:
        ValueError: Si la cadena no puede convertirse a un booleano.
    """
    if s.lower() in ['true', 'false']:
        return s.lower() == 'true'
    raise ValueError(f"No se puede convertir la cadena {s} a un valor booleano.")
    

def str_to_json(s):
    """
    Convierte una cadena a un objeto JSON.
    
    Args:
        s (str): La cadena a convertir.
    
    Returns:
        object: El objeto JSON correspondiente.
    
    Raises:
        ValueError: Si la cadena no puede convertirse a JSON.
    """
    try:
        return json.loads(s)
    except json.JSONDecodeError as e:
        raise ValueError(f"No se puede convertir la cadena {s} a formato JSON.") from e

def getenv(var_name, default_value):
    """
    Busca una variable de entorno y devuelve su valor en el tipo correspondiente.
    Si la variable no se encuentra, devuelve el valor por defecto.
    
    Args:
        var_name (str): Nombre de la variable de entorno.
        default_value: Valor por defecto si la variable de entorno no se encuentra.
        
    Returns:
        El valor de la variable de entorno en el tipo correspondiente o el valor por defecto.
    """
    
    # Lista de funciones de conversión en orden de prioridad
    conversion_funcs = [
        int,
        float,
        str_to_bool,
        str_to_json
    ]
    
    # Obtener el valor de la variable de entorno
    value = os.getenv(var_name)
    
    # Si la variable de entorno no existe, devolver el valor por defecto
    if value is None:
        logger.warning(f'No se encontro la variable de entorno [{var_name}], se usara el valor por defecto [{default_value}].')
        return default_value
    
    # Intentar convertir el valor usando las funciones de conversión
    for func in conversion_funcs:
        try:
            # Si la conversión tiene éxito, devolver el valor convertido
            return func(value)
        except ValueError:
            # Si la conversión falla, continuar con la siguiente función
            continue
    
    # Si ninguna conversión tiene éxito, devolver el valor como cadena
    return value

def generate_random_user_agent(usr_agent_type=None):
    """
    Genera un User Agent aleatorio.

    Args:
        usr_agent_type (int, optional): El tipo de User Agent. 0 para Chrome, 1 para Firefox, 2 para Safari, 3 para Edge, 4 para Opera.
                                        Si no se proporciona, se elige aleatoriamente entre 0 y 4.

    Returns:
        str: El User Agent generado.
    
    Raises:
        ValueError: Si usr_agent_type no es un tipo válido.
    """
    # Verifica si se proporcionó un tipo de User Agent
    if usr_agent_type is None:
        usr_agent_type = random.randint(0, 4)

    # Diccionario de formatos de User Agent
    user_agent_formats = {
        0: f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(90, 128)}.0.0.0 Safari/537.36',
        1: f'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{random.randint(90, 128)}.0) Gecko/20100101 Firefox/{random.randint(90, 128)}.0',
        2: f'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/{random.randint(90, 128)}.0',
        3: f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(90, 128)}.0.0.0 Edg/{random.randint(90, 128)}.0.0 Safari/537.36',
        4: f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(90, 128)}.0.0.0 OPR/{random.randint(90, 128)}.0.0 Safari/537.36'
    }

    # Verifica si el tipo de User Agent es válido y retorna el User Agent correspondiente
    if usr_agent_type in user_agent_formats:
        return user_agent_formats[usr_agent_type]
    else:
        min_key = min(user_agent_formats.keys())
        max_key = max(user_agent_formats.keys())
        raise ValueError(f'El tipo de User Agent debe ser un número entre {min_key} y {max_key}.')

def get_time_len(tiempo=0, unit="hours", input_format="seconds", output_format="str", verbose=False):
    """
    Convierte una cantidad de tiempo en diferentes unidades de tiempo.

    Args:
        tiempo (int, str): Cantidad de tiempo a convertir. Puede ser un número entero o una cadena.
        unit (str): Unidad de tiempo en la que se desea obtener el resultado.
                    Puede ser "seconds", "minutes", "hours" o "days".
                    Por defecto, se devuelve en horas.
        input_format (str): Formato de entrada del tiempo. Puede ser "seconds", "minutes", "hours" o "days".
                            Por defecto, se asume que el tiempo está en segundos.
        output_format (str): Formato de salida del tiempo. Puede ser "str" (cadena de texto) o "float" (valor numérico).
                                Por defecto, se devuelve en formato de cadena.

    Returns:
        str or float: La cantidad de tiempo convertida en la unidad especificada,
                        o en formato de cadena "HH:MM:SS" si output_format es "str".
    """
    conversiones = {
        "seconds": 1,
        "minutes": 60,
        "hours": 3600,
        "days": 86400
    }

    try:
        if isinstance(tiempo, str):
            tiempo = int(tiempo)
        elif not isinstance(tiempo, int):
            raise TypeError("El tiempo debe ser un número entero o una cadena que represente un número entero.")

        if tiempo < 0:
            raise ValueError("El tiempo a formatear debe ser un valor no negativo.")

        if input_format in conversiones:
            tiempo_en_segundos = tiempo * conversiones[input_format]
        else:
            raise ValueError("El formato de entrada especificado no es válido.")

        if unit in conversiones:
            resultado = tiempo_en_segundos / conversiones[unit]
        else:
            raise ValueError("La unidad de conversion especificada no es válida.")

        if output_format == "str":
            horas, segundos_restantes = divmod(tiempo_en_segundos, 3600)
            minutos, segundos = divmod(segundos_restantes, 60)
            return f"{horas:02d}:{minutos:02d}:{segundos:02d}"
        elif output_format == "float":
            return resultado
        else:
            raise ValueError("El formato de salida especificado no es válido.")

    except (TypeError, ValueError) as e:
        if verbose:
            logger.error(f"Error: {e}. Asegúrese de proporcionar valores válidos para el tiempo, el formato de entrada y la unidad.")
        return 0

def get_formatted_date(format_str="%Y%m%d_%H%M%S", verbose=DEFAULT_UTILS_VERBOSE):
    """
    Devuelve la fecha y hora actual formateada según el formato especificado.

    Args:
        format_str (str): El formato deseado para la fecha y hora. Por defecto, es "%Y%m%d_%H%M%S".

    Returns:
        str: La fecha y hora actual formateada.
    """
    try:
        current_datetime = datetime.now()
        formatted_date = current_datetime.strftime(format_str)
        return formatted_date
    except Exception as e:
        if verbose:
            logger.error(f"Error al obtener la fecha y hora formateada. Error: {e}")
        return None
    
def get_dir_files(path, pattern=None, verbose=DEFAULT_UTILS_VERBOSE):
    """
    Obtener los archivos dentro de un directorio.

    Args:
        path (str): Ruta del directorio.
        pattern (str, optional): Patrón para filtrar determinados archivos. Por defecto, es None.

    Returns:
        list: Lista de archivos dentro del directorio que coinciden con el patrón, si se proporciona.
    """
    try:
        # Verificar si la ruta del directorio es válida
        if not Path(path).is_dir():
            raise ValueError(f"La ruta especificada '{path}' no es un directorio válido.")

        # Obtener los nombres de los archivos en el directorio
        file_list = os.listdir(path)

        # Filtrar los nombres si se proporciona un patrón
        if pattern is not None:
            file_list = [x for x in file_list if pattern in x]

        return file_list
    except Exception as e:
        if verbose:
            logger.error(f"Error al obtener los archivos del directorio. Error: {e}")
        return None

def get_date_from_filename(filename, date_pattern=r'(\d{8})_(\d{6})', verbose=DEFAULT_UTILS_VERBOSE):
    """
    Obtiene la fecha y hora de un nombre de archivo utilizando expresiones regulares.

    Args:
        filename (str): El nombre del archivo del cual extraer la fecha y hora.
        date_pattern (str, optional): El patrón de fecha para buscar en el nombre del archivo.
                                        Por defecto, es r'(\d{8})_(\d{6})'.

    Returns:
        tuple: Una tupla con la fecha (YYYYMMDD) y la hora (HHMMSS) extraídas del nombre del archivo.
                Si no se encuentra una coincidencia, devuelve ('00000000', '000000').
    """
    try:
        # Aplicar el patrón de fecha
        res = re.search(date_pattern, filename)

        # Devolver el resultado buscado
        if res:
            date, time = res.groups()
            if '00000000' <= date <= '99991231' and '000000' <= time <= '235959':
                return (date, time)
        
        # Si no se encuentra una coincidencia válida, devolver el valor predeterminado
        return ('00000000', '000000')
    except Exception as e:
        if verbose:
            logger.error(f"Error al obtener la fecha y hora del nombre del archivo. Error: {e}")
        return ('00000000', '000000')

def get_newest_file(filename_list, date_pattern=r'(\d{8})_(\d{6})', verbose=DEFAULT_UTILS_VERBOSE):
    """
    Encuentra el archivo más reciente en una lista de nombres de archivos.

    Args:
        filename_list (list): Una lista de nombres de archivos.
        date_pattern (str, optional): El patrón de fecha para buscar en los nombres de archivo.
                                        Por defecto, es r'(\d{8})_(\d{6})'.

    Returns:
        str or None: El nombre del archivo más reciente, o None si no se encontraron archivos en el formato esperado.
    """
    try:
        if not filename_list:
            if verbose:
                logger.error("La lista de nombres de archivos está vacía.")
            return None

        # Filtrar los nombres de archivo que no coinciden con el patrón de fecha especificado
        valid_filenames = [filename for filename in filename_list if re.search(date_pattern, filename)]

        if not valid_filenames:
            if verbose:
                logger.error("No se encontraron archivos en el formato esperado.")
            return None

        newest_file = max(valid_filenames, key=lambda x: get_date_from_filename(x, date_pattern=date_pattern)[1])
        return newest_file
    except Exception as e:
        if verbose:
            logger.error(f"Error al obtener el archivo más reciente. Error: {e}")
        return None
    
def is_url_arg(text):
    """
    Verifica si una cadena de texto representa una URL.

    Args:
        arg (str): La cadena de texto a verificar.

    Returns:
        bool: True si la cadena representa una URL, False en caso contrario.
    """
    url_pattern = re.compile(
        r'^(https?://)?'                 # protocolo opcional
        r'(([\w-]+\.)+[\w-]{2,})'        # subdominio(s) opcionales y dominio de nivel superior
        r'(:\d+)?'                       # puerto opcional
        r'(/.*)?$'                       # ruta opcional
    )
    return bool(url_pattern.match(text))

def safe_get_from_json(dct, keys, default=None):
    """
    Obtiene de manera segura un valor de un diccionario anidado. 
    Si alguna clave en la ruta no se encuentra, devuelve el valor por defecto.

    Args:
        dct (dict): El diccionario del cual obtener el valor.
        keys (list): La lista de claves que indican la ruta del valor en el diccionario.
        default: El valor por defecto a devolver si alguna clave no se encuentra.

    Returns:
        El valor encontrado en el diccionario, o el valor por defecto si alguna clave no se encuentra.
    """
    for key in keys:
        if not isinstance(dct, dict) or key not in dct:
            return default
        dct = dct[key]
    return dct

def fit_time_to_24_hours(tiempo, verbose=DEFAULT_UTILS_VERBOSE):
    """
    Convierte una duración en formato 'horas:minutos:segundos' a 'días:horas:minutos:segundos'.

    Args:
        tiempo (str): La duración en formato 'horas:minutos:segundos'.
        verbose (bool): Si es True, imprime mensajes de error detallados.

    Returns:
        str: La duración convertida en formato 'días:horas:minutos:segundos', o '0:00:00:00' si el formato de entrada es incorrecto.
    """
    try:
        horas, minutos, segundos = map(int, tiempo.split(':'))
        
        # Validación de valores
        if not (0 <= segundos < 60):
            raise ValueError
        if not (0 <= minutos < 60):
            raise ValueError
        
        total_segundos = horas * 3600 + minutos * 60 + segundos
        
        dias = total_segundos // (24 * 3600)
        horas_res = (total_segundos % (24 * 3600)) // 3600
        minutos_res = (total_segundos % 3600) // 60
        segundos_res = total_segundos % 60
        
        return f"{dias}:{horas_res:02}:{minutos_res:02}:{segundos_res:02}"
    except ValueError:
        if verbose:
            logger.error(f"La entrada [{tiempo}] tiene un formato de duración incorrecto. Debe ser 'horas:minutos:segundos' con minutos y segundos entre 0 y 59.")
        return '0:00:00:00'
    
def time_to_seconds(tiempo, verbose=DEFAULT_UTILS_VERBOSE):
    """
    Convierte una duración en formato 'horas:minutos:segundos' a la cantidad total de segundos.

    Args:
        tiempo (str): La duración en formato 'horas:minutos:segundos'.
        verbose (bool): Si es True, imprime mensajes de error detallados.

    Returns:
        int: La cantidad total de segundos, o 0 si el formato de entrada es incorrecto.
    """
    try:
        horas, minutos, segundos = map(int, tiempo.split(':'))
        
        # Validación de valores
        if not (0 <= segundos < 60):
            raise ValueError
        if not (0 <= minutos < 60):
            raise ValueError
        if not (0 <= horas < 24):
            raise ValueError
        
        total_segundos = horas * 3600 + minutos * 60 + segundos
        return total_segundos
    except ValueError:
        if verbose:
            logger.error(f"La entrada [{tiempo}] tiene un formato de duración incorrecto. Debe ser 'horas:minutos:segundos' con horas entre 0 y 23 y minutos y segundos entre 0 y 59.")
        return 0

def transform_duration_format(duracion_iso, verbose=DEFAULT_UTILS_VERBOSE):
    """
    Transforma una duración en formato ISO 8601 en un formato de tiempo más legible (HH:MM:SS).

    Args:
        duracion_iso (str): La duración en formato ISO 8601, por ejemplo, 'P1DT2H3M4S'.

    Returns:
        str: La duración transformada en formato 'HH:MM:SS' o un mensaje de error si la entrada no está en el formato correcto.

    Example:
        >>> transform_duration_format('P1DT2H3M4S')
        '26:03:04'
    """
    try:
        # Utilizar expresiones regulares para extraer componentes de la duración
        match = re.match(r'P(?:([0-9]+)D)?T(?:([0-9]+)H)?(?:([0-9]+)M)?(?:([0-9]+)S)?', duracion_iso)

        # Verificar si la duración está en el formato correcto
        if not match:
            raise ValueError(f"La duración proporcionada [{duracion_iso}] no está en formato ISO 8601.")

        # Extraer componentes de la duración (días, horas, minutos, segundos)
        dias, horas, minutos, segundos = map(
            lambda x: int(x) if x else 0, match.groups())

        # Crear un objeto timedelta
        duracion_timedelta = timedelta(days=dias, hours=horas, minutes=minutos, seconds=segundos)

        # Formatear como HH:MM:SS con dos dígitos en cada componente
        duracion_formateada = "{:02}:{:02}:{:02}".format(
            duracion_timedelta.days * 24 + duracion_timedelta.seconds // 3600,
            (duracion_timedelta.seconds % 3600) // 60,
            duracion_timedelta.seconds % 60
        )
        return duracion_formateada
    
    except AssertionError as e:
        if verbose:
            logger.error(f"Error (AssertionError) al intentar formatear el tiempo [{duracion_iso}]: {e}")
        return '00:00:00'
    except ValueError as e:
        if verbose:
            logger.error(f"Error (ValueError) al intentar formatear el tiempo [{duracion_iso}]: {e}")
        return '00:00:00'
    except Exception as e:
        if verbose:
            logger.error(f"Error (Exception) al intentar formatear el tiempo [{duracion_iso}]: {e}")
        return '00:00:00'

def get_similarweb_url_tuple(domain, verbose=DEFAULT_UTILS_VERBOSE):
    """
    Genera una tupla de URL y alias para el dominio dado.

    Args:
        domain (str): El nombre de dominio para el cual se generará la URL.
        verbose (bool, optional): Flag que indica si se deben imprimir mensajes detallados en caso de error. Por defecto es False.

    Returns:
        tuple: Una tupla que contiene la URL y el alias generados. Si no se puede generar la tupla, se devuelve (None, None).

    Note:
        La URL generada estará en el formato '{SIMILARWEB_BASE_URL}/website/{domain}/#overview'.
        El alias se generará reemplazando los puntos en el nombre de dominio con guiones bajos.

    Example:
        url, alias = get_similarweb_url_tuple('example.com', verbose=True)
    """
    try:
        # Validar el formato del nombre de dominio
        if not isinstance(domain, str) or not domain:
            raise ValueError("El nombre de dominio proporcionado no es válido (no es un string o es nulo).")
        
        # Verifico que la entrada sea una URL
        if not is_url_arg(domain):
            raise ValueError("El nombre de dominio proporcionado no es válido (no cumple con el formato URL).")

        # Reemplazar dobles barras con una sola barra
        domain = domain.replace('//', '/')

        # Generar la URL con el formato adecuado
        url = f'{SIMILARWEB_BASE_URL}/website/{domain}/#overview'

        # Generar el alias reemplazando los puntos con guiones bajos
        alias = domain.replace('.', '_')

        return url, alias
    except ValueError as ve:
        # Capturar errores de valor incorrecto
        if verbose:
            logger.error(f"Error (ValueError) al generar la tupla de URL para el dominio [{domain}]. Error: {ve}")
        return None, None
    except Exception as e:
        # Capturar otros errores inesperados
        if verbose:
            logger.error(f"Error (Exception) al generar la tupla de URL para el dominio [{domain}]. Error: {e}")
        return None, None
    
def join_str(string, separator=',', format_db=False):
    """
    Une una cadena individual o una lista de cadenas utilizando el separador especificado.

    Args:
    - string: Cadena individual o lista de cadenas a unir.
    - separator: (Opcional) El separador utilizado para unir las cadenas. Por defecto es ','.

    Returns:
    - Una cadena única que resulta de unir las cadenas de la entrada con el separador especificado.
    """
    try:
        if string is None:  # Verifica si la entrada es None
            return ''
        elif isinstance(string, str):  # Verifica si la entrada es una cadena individual
            return string if string else ''
        elif isinstance(string, list):  # Verifica si la entrada es una lista
            if format_db:
                if len(string) == 1:
                    return f'"{string[0]}"'
                else:
                    return separator.join(f'"{item}"' for item in string)
            else:
                return separator.join(map(str, string))  # Convertir todos los elementos a cadena antes de unirlos
        else:
            logger.error(f"La entrada {string} debe ser una cadena individual, una lista de cadenas o None.")
            return ''
    except Exception as e:
        logger.error(f"Error inesperado al procesar la cadena de caracteres {string}. Error: {e}")
        return ''
    
def elements_to_kwargs(*args, **kwargs):
    """
    Convierte una cantidad indefinida de elementos a un diccionario de argumentos de palabras clave (**kwargs).

    Argumentos:
    *args: Tuplas de dos elementos donde el primer elemento es el nombre y el segundo es el valor.
    **kwargs: Argumentos de palabras clave adicionales.

    Retorna:
    dict: Un diccionario que contiene todos los argumentos como claves y valores.
    
    Ejemplo:
    elements_to_kwargs(('a', 1), ('b', 2), c=3, d=4)  # {'a': 1, 'b': 2, 'c': 3, 'd': 4}
    """
    # Crear un diccionario vacío que contendrá los kwargs resultantes
    kwargs_resultants = {}

    # Iterar sobre los argumentos posicionales (args) si los hay
    for i, arg in enumerate(args):
        # Cada argumento debe ser una tupla (nombre, valor)
        if isinstance(arg, tuple) and len(arg) == 2:
            kwargs_resultants[arg[0]] = arg[1]
        else:
            raise TypeError(f"El argumento en la posición {i} no es una tupla de dos elementos (nombre, valor).")

    # Agregar los kwargs adicionales provenientes de kwargs
    kwargs_resultants.update(kwargs)

    return kwargs_resultants

def get_param(target='', default=None, args_pos=0, *args, **kwargs):
    """
    Obtiene un parámetro desde diferentes fuentes:
    1. Desde kwargs si está presente y coincide con el 'target'.
    2. Desde args tomando la posición indicada por 'args_pos' si está presente.
    3. Usa el valor predeterminado si no se encuentra en ninguna fuente.

    Argumentos:
    target (str): Nombre del parámetro objetivo en kwargs.
    default: Valor predeterminado del parámetro.
    args_pos (int): Índice del argumento en args que se usará si no se encuentra en kwargs.
    *args: Argumentos posicionales.
    **kwargs: Argumentos de palabras clave.

    Retorna:
    El valor del parámetro obtenido.
    """
    try:
        value = kwargs.get(target, default)  # Intentar obtener desde kwargs usando el 'target'
        if value is default and args:
            # Si no se encuentra en kwargs y hay args, intentar obtenerlo de la posición en args indicada por args_pos
            if 0 <= args_pos < len(args):
                value = args[args_pos]

        return value
    except Exception as e:
        # Capturar cualquier excepción y elevarla con un mensaje descriptivo
        raise ValueError(f"Error al obtener el parámetro: {str(e)}")

def is_video_online(video_id):
    """
    Verifica si un video de YouTube está disponible usando el endpoint oEmbed.

    :param video_id: str: ID del video de YouTube
    :return: bool: True si el video está disponible, False en caso contrario
    """
    # Construir la URL usando el video ID proporcionado
    url = f'https://www.youtube.com/oembed?url=http://www.youtube.com/watch?v={video_id}&format=json'
    
    # Realizar una solicitud GET a la URL
    response = requests.get(url)

    # Si la respuesta tiene un código de estado 200, el video está disponible
    if response.status_code == 200:
        return True
    # Si la respuesta tiene un código de estado 403, el video no está disponible
    elif response.status_code == 403:
        return False
    else:
        # Puedes manejar otros códigos de estado si es necesario
        return False

################################################################################
# LLEGUE HASTA ACA CON LA OPTIMIZACION
################################################################################
def o_fmt_error(error_code=None, error_message=None, ref_code=None, filename=None):
    # Get current date
    import datetime
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Si no se provee un codigo o un mensaje de error abortar escritura
    if((error_code is None) or (error_message is None)):
        return
    # Open error log file
    if filename is None:
        filepath = os.environ.get("SOFT_LOGS")
        filename = (filepath if filepath is not None else 'logs') + "/error_log.txt"
    with open(filename, "a", encoding='utf-8') as error_log_file:
        # Add header to error log
        error_log_file.write("=" * 80 + "\n")
        error_log_file.write("=" * 20 + " " * 14 + "SYSTEM ERROR" + " " * 14 + "=" * 20 + "\n")
        error_log_file.write("=" * 80 + "\n")
        # Add date to error log
        error_log_file.write("\n")
        error_log_file.write(f"Date: {date}\n")
        error_log_file.write("\n")
        # Add user message to error log
        error_log_file.write(f"Error Message: {error_message}\n")
        # Add reference message to error log
        error_log_file.write("\n")
        error_log_file.write(f"Reference Code: {ref_code}-{error_code}\n")
        error_log_file.write("\n")
        #
        error_log_file.close()

def cprint(msg, logfile=None):
    # Get current date
    import datetime
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Open console log file
    filepath = os.environ.get("SOFT_LOGS")
    if logfile is None:
        filename = filepath + "/console_log.txt"
    else:
        filename = logfile
    with open(filename, "a", encoding='utf-8') as console_log_file:
        print(msg)
        console_log_file.write(date + ': ' + msg + "\n")
        console_log_file.close()