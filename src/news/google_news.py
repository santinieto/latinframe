# Imports estándar de Python
import os
# import sys

# Añade el directorio raíz del proyecto a sys.path
# current_path = os.path.dirname(os.path.abspath(__file__))
# project_root = os.path.abspath(os.path.join(current_path, '..', '..'))  # Ajusta según la estructura de tu proyecto
# sys.path.append(project_root)

# Imports de terceros
import re
import urllib.parse
import requests
from functools import partial
from multiprocessing import Pool, cpu_count
from bs4 import BeautifulSoup
import time
from unidecode import unidecode

# Imports locales
from src.news.new import New
from src.logger.logger import Logger
from src.utils.utils import get_http_response, getenv
from src.database.db import Database
from datetime import datetime, timedelta

################################################################################
# Genero una instancia del Logger
################################################################################
logger = Logger(os.path.basename(__file__)).get_logger()

# Define tu función de inicialización de cada objeto
def init_google_new(html_content):
    """
    Inicializa un objeto de la clase que corresponda.

    Args:
        html_content (str): Contenido HTML del cual extraer datos.

    Returns:
        El objeto del tipo correspondiente ya inicializado.
    """
    item = GoogleNew()
    item.set_html(html_content)
    item.fetch_data()
    return item

class GoogleNewsListings:
    ############################################################################
    # Atributos globables
    ############################################################################
    # Atributo de clase para almacenar la instancia única
    _instance = None
    
    DEFAULT_SAVE_HTML = False
    DEFAULT_ENABLE_MP = True
    DEFAULT_N_CORES = -1
    DEBUG = False
    
    DEFAULT_TOPICS = [
        'juguetes',
        'disney',
        'pixar',
        'Pixar'
    ]
    
    ############################################################################
    # Metodos de incializacion
    ############################################################################
    # Cuando solicito crear una instancia me aseguro que
    # si ya hay una creada, devuelvo esa misma
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, topics):
        if not hasattr(self, 'initialized'):
            self.topics = []
            self.listings = {}
            self.urls = {}
            self.save_html = getenv('NEWS_SAVE_HTML', self.DEFAULT_SAVE_HTML)
            self.enable_mp = getenv('ENABLE_MP', self.DEFAULT_ENABLE_MP)
            self.n_cores = self.set_n_cores()
            
            # Defino una lista por defecto y
            # agrego las tematicas de interes
            self.add_topics(self.DEFAULT_TOPICS)
            self.add_topics(topics)

            # Inicializar el objeto Pool para el procesamiento paralelo
            if self.enable_mp:
                self.pool = Pool(processes=self.n_cores)
            else:
                self.pool = None
            
            self.initialized = True
    
    def set_n_cores(self):
        """
        Obtiene el número de procesos a utilizar según la configuración.
        """
        max_n_cores = cpu_count()
        if getenv('MP_N_CORES', self.DEFAULT_N_CORES) < 0:
            return max_n_cores
        else:
            if getenv('MP_N_CORES', self.DEFAULT_N_CORES) > max_n_cores:
                return max_n_cores
            else:
                return getenv('MP_N_CORES', self.DEFAULT_N_CORES)

    ############################################################################
    # Metodos de de uso
    ############################################################################
    def add_topics(self, topics):
        """
        Agrega las tematicas, convirtiendo una cadena en una lista y evitando duplicados.
        """
        try:
            if isinstance(topics, str):
                topics = [topics]
            elif not isinstance(topics, list):
                raise ValueError("El argumento 'topics' debe ser una cadena o una lista.")
            
            # Paso todo a minusculas para evitar duplicados
            topics = [x.lower() for x in topics]

            # Agrego las tematicas a la lista y me aseguro que no haya repetidos
            self.topics = list(set(self.topics + topics))
            
            if self.DEBUG:
                logger.info(f'Se han añadido tematicas a la clase.\nLista actual: {self.topics}')
            
        except ValueError as e:
            logger.error(f'No se pudo agregar la lista de temas [{topics}]. Error: {e}.')

    def generate_urls(self):
        """
        Genera las URLs para cada tema.
        """
        if not self.topics:
            logger.warning("No hay temáticas desde las cuales obtener datos.")
            return
        
        # Reinicio el diccionario de tematicas
        self.urls = {}
        
        # Para cada tema genero la URL
        for topic in self.topics:
            
            if not isinstance(topic, str):
                logger.warning(f'La tematica [{topic}] no es una cadena de texto y será omitida.')
                continue
            
            # Conformo la URL propiamente dicha
            encoded_topic = urllib.parse.quote_plus(topic)
            url = f'https://www.google.com/search?q={encoded_topic}&tbm=nws'
            
            # Guardo los datos generados
            self.listings[topic] = {'topic': topic, 'url': url}
            self.urls[topic] = url
            
            if self.DEBUG:
                logger.info(f'URL generada para la tematica [{topic}]: [{url}]')

    def fetch_html_content(self):
        """
        Obtiene el contenido HTML de cada URL generada.
        """
        # Para cada tematica voy a obtener el contenido HTML
        for topic in self.topics:
            try:
                
                # Me aseguro que la tematica tiene una URL generada y la obtengo
                if topic in self.listings:
                    
                    # Obtengo el contenido HTML
                    url = self.listings[topic]['url']
                    response = get_http_response(url)
                    
                    if response:
                        self.listings[topic]['html_content'] = response
                        
                        # Menssaje de debug
                        if self.DEBUG:
                            logger.info(f'Contenido HTML obtenido para la tematica [{topic}].')
                        
                    else:
                        self.listings[topic]['html_content'] = None
                        logger.error(f"Error al obtener el contenido HTML para [{topic}]: No se pudo obtener respuesta HTTP desde [{url}]")
                        
                else:
                    logger.error(f"No se encontró la clave [{topic}] en el diccionario de listados.")
            
            except requests.RequestException as e:
                logger.error(f"Error al obtener el contenido HTML para [{topic}]. Error: {e}")
            except Exception as e:
                logger.error(f"Error inesperado al obtener el contenido HTML para [{topic}]. Error: {e}")

    def find_items(self):
        """
        Scrapea el contenido HTML de cada URL y crea objetos segun el tipo que corresponda.
        """
        for topic in self.topics:
            if 'html_content' in self.listings[topic]:
                html_content = self.listings[topic]['html_content']
                
                # Obtengo los items encontrados
                # NOTA: Aca es donde hay que cambiar para aplicar el filtro correcto
                html_contents = html_content.find_all('div', class_=['CA8QAA','SoaBEf','xCURGd'])
                
                if self.enable_mp:
                    # Procesamiento en paralelo
                    self.parallel_item_initialize(topic, html_contents)
                else:
                    # Procesamiento en serie
                    self.serial_item_initialize(topic, html_contents)
                    
                # Le asigno la tematica correspondientea cada item
                for item in self.listings[topic]['items']:
                    item.topic = topic
                
            else:
                logger.error(f"El contenido HTML para la tematica [{topic}] es None, no se pueden buscar informacion.")

    def parallel_item_initialize(self, topic, html_contents):
        """
        Inicializa los objetos utilizando multiprocessing.Pool.
        """
        try:
            # Paso el contenido a string porque sino, no puede procesar en paralelo
            html_contents = [str(x) for x in html_contents]
            init_func = partial(init_google_new)
            self.listings[topic]['items'] = self.pool.map(init_func, html_contents)
        except Exception as e:
            logger.error(f'Error al inicializar los objetos en paralelo. Error: {str(e)}')

    def serial_item_initialize(self, topic, html_contents):
        """
        Inicializa los objetos de forma serial.
        """
        try:
            self.listings[topic]['items'] = [init_google_new(str(html_content)) for html_content in html_contents]
        except Exception as e:
            logger.error(f'Error al inicializar los objetos en serie. Error: {str(e)}')

    def show_items_content(self):
        """
        Muestra el contenido de cada item para cada tematica.
        """
        for topic, listing in self.listings.items():
            news = listing.get('items')
            if news:
                logger.info(f"Contenido de las noticias para la tematica [{topic}]:")
                for new in news:
                    logger.info(str(new))
            else:
                logger.info(f"No se encontraron noticias en el objeto GoogleNewsListing para la temática {topic}.")

    def fetch_data(self):
        """
        Funcion principal de ejecucion.
        """
        self.generate_urls()
        self.fetch_html_content()
        self.find_items()
        # self.show_items_content()
        
    def get_news(self):
        news_list = []
        for topic, listing in self.listings.items():
            news = listing.get('items')
            if news:
                news_list = news_list + news
        return news_list

class GoogleNew(New):
    def __init__(self, new_id=None, info_dict=None):
        # Actualiza los valores por defecto específicos de GoogleNew
        updated_defaults = {
        }
        
        # Combina los valores por defecto de New con los específicos de GoogleNew
        if info_dict:
            info_dict = {**updated_defaults, **info_dict}
        else:
            info_dict = updated_defaults
        
        # Inicializa la clase base con los valores combinados
        super().__init__(new_id, info_dict)
        self.data_loaded = False
        
    def set_html(self, html_content):
        """
        Establece el contenido HTML de la noticia.

        Args:
            html_content (str): Contenido HTML a establecer.
        """
        if isinstance(html_content, str):
            html_content = BeautifulSoup(html_content, 'html.parser')
        self.html_content = html_content
        
        if self.new_id is None:
            self.new_id = 1
            
        if self.new_id:
            if self.DEBUG:
                logger.info(f"Contenido HTML establecido con éxito para la noticia {self.new_id}.")
        else:
            self.html_content = None
            logger.error(f"No se establecio el contenido HTML para la noticia dado que no se encontro el ID.\n\nHTML\n\n{html_content}")

    ############################################################################
    # Actualizar los datos de la noticia
    ############################################################################
    def fetch_data(self, info_dict=None, force_method=None):
        """
        Intenta cargar datos de la noticia utilizando diferentes métodos.

        El orden de preferencia para cargar los datos es el siguiente:
        1. Datos proporcionados durante la inicialización del objeto.
        2. Utilización de alguna API.
        3. Scraping de contenido HTML.

        Si alguno de los métodos falla, se pasará automáticamente al siguiente método.

        Args:
            info_dict (dict): Diccionario con datos de la noticia para cargar.
            force_method (str): Método para forzar la carga de datos ('api' para la utilizacion de una API, 'html' para scraping HTML).

        Returns:
            bool: True si se cargaron los datos con éxito, False en caso contrario.
        """
        # Verifica si los datos ya están cargados
        if self.data_loaded:
            logger.info(f"Los datos de la noticia {self.new_id} ya están cargados en el objeto GoogleNew.")
            self.fetch_status = True
            return

        # Intenta cargar datos del diccionario proporcionado durante la inicialización
        if info_dict:
            self.load_from_dict(info_dict)
            logger.info(f"Los datos de la noticia {self.new_id} se cargaron exitosamente desde el diccionario proporcionado durante la inicialización.")
            self.fetch_status = True
            return

        # Verifica si se especificó un método forzado
        if force_method:
            logger.info(f"Los datos de la noticia {self.new_id} se van a cargar forzadamente usando el metodo {force_method}.")
            
            if force_method.lower() == 'api':
                if self._load_data_from_api():
                    self.fetch_status = True
                    return
            elif force_method.lower() == 'html':
                if self._load_data_from_html():
                    self.fetch_status = True
                    return
            else:
                logger.warning("Método de carga forzada no válido. Ignorando solicitud.")
                self.fetch_status = False
                return
            
            logger.error(f"No se pudo cargar datos de la noticia {self.new_id} de Ebay usando metodos forzados.")
            self.fetch_status = False
            return

        # Intenta cargar datos utilizando la API de Ebay si no se especifica un método forzado
        if self._load_data_from_api():
            self.fetch_status = True
            return

        # Intenta cargar datos mediante scraping de contenido HTML si no se especifica un método forzado
        if self._load_data_from_html():
            self.fetch_status = True
            return

        # Si no se pudo cargar datos de ninguna manera, registra un mensaje de error
        logger.error(f"No se pudo cargar datos de la noticia {self.new_id} de Ebay.")
        self.fetch_status = False
        return
    
    ############################################################################
    # Obtencion de datos mediante una API
    ############################################################################
    def _load_data_from_api(self):
        return False
    
    ############################################################################
    # Obtencion de datos mediante el codigo HTML
    ############################################################################
    def _load_data_from_html(self):
        """
        Intenta cargar datos utilizando el scraping de contenido HTML.

        Returns:
            bool: True si se cargaron los datos con éxito, False en caso contrario.
        """
        try:
            # Si no tengo contenido HTML lo intento cargar
            if self.html_content is None:
                self.fetch_html_content()
                
            # Si hubo un fallo al obtener el codigo HTML de la noticia, logeo un
            # error y salgo de la funcion
            if self.html_content in [False, None]:
                logger.error(f"No se dispone de contenido HTML para la noticia {self.new_id}.")
                return False
                
            if self.save_html:
                self.save_html_content()
            
            # Busco la antiguedad de antemano porque la necesito para la fecha
            # de publicacion
            self.antique = self.fetch_new_antique()
            
            # Crear el diccionario para los datos
            new_data = {
                'new_id': self.new_id, # Tiene que estar siempre este campo
                'url': self.fetch_new_url(),
                'title': self.fetch_new_title(),
                'topic_id': self.fetch_new_topic_id(),
                'newspaper': self.fetch_new_newspaper(),
                'newspaper_id': self.fetch_new_newspaper_id(),
                'publish_date': self.fetch_new_publish_date(),
                }
            
            # Actualiza la información de la noticia con los datos obtenidos del scraping
            self.load_from_dict(new_data)
            
            # Mensaje de debug
            if self.DEBUG:
                logger.info("Los datos se cargaron exitosamente mediante scraping de contenido HTML.")
            return True
        
        except Exception as e:
            logger.warning(f"Fallo al cargar datos mediante scraping de contenido HTML: {e}")

        return False
    
    def fetch_new_url(self):
        """
        """
        # Verificar si hay contenido HTML disponible
        if self.html_content is None:
            logger.error("No se puede obtener la URL de la noticia sin contenido HTML.")
            return self.DEFAULT_VALUES['url']
        
        # Inicializar valor predeterminado
        url = self.DEFAULT_VALUES['url']
        
        try:
            url = self.html_content.find('a').get('href')
        except AttributeError:
            logger.error("No se pudo obtener la URL de la noticia: No se encontro el tag de titulo.")

        return url
    
    def fetch_new_title(self):
        """
        """
        # Verificar si hay contenido HTML disponible
        if self.html_content is None:
            logger.error("No se puede obtener el titulo de la noticia sin contenido HTML.")
            return self.DEFAULT_VALUES['title']
        
        # Inicializar valor predeterminado
        title = self.DEFAULT_VALUES['title']
        
        try:
            title = self.html_content.find('div', class_='n0jPhd ynAwRc MBeuO nDgy9d').text
            title = unidecode( title ) # Quito los acentos
            title = title.replace('\n','')
            title = title.replace('"', '')
            title = title.replace("'", '')
        except AttributeError:
            logger.error("No se pudo obtener el titulo de la noticia: No se encontro el tag de titulo.")

        return title
    
    def fetch_new_topic_id(self):
        return None
    
    def fetch_new_newspaper(self):
        """
        """
        # Verificar si hay contenido HTML disponible
        if self.html_content is None:
            logger.error("No se puede obtener el periodico de la noticia sin contenido HTML.")
            return self.DEFAULT_VALUES['newspaper']
        
        # Inicializar valor predeterminado
        newspaper = self.DEFAULT_VALUES['newspaper']
        
        try:
            newspaper = self.html_content.find('div', class_='MgUUmf NUnG9d').text
            newspaper = unidecode( newspaper ) # Quito los acentos
            newspaper = newspaper.replace('\n','')
            newspaper = newspaper.replace('"', '')
            newspaper = newspaper.replace("'", '')
        except AttributeError:
            logger.error("No se pudo obtener el periodico de la noticia: No se encontro el tag de titulo.")

        return newspaper
    
    def fetch_new_newspaper_id(self):
        return None
    
    def fetch_new_antique(self):
        """
        """
        # Verificar si hay contenido HTML disponible
        if self.html_content is None:
            logger.error("No se puede obtener la antiguedad de la noticia sin contenido HTML.")
            return self.DEFAULT_VALUES['antique']
        
        # Inicializar valor predeterminado
        antique = self.DEFAULT_VALUES['antique']
        
        try:
            antique = self.html_content.find('div', class_='OSrXXb rbYSKb LfVVr')
            if antique:
                return antique.text
            
            antique = self.html_content.find('div', class_='OSrXXb rbYSKb')
            if antique:
                return antique.text
        except AttributeError:
            logger.error("No se pudo obtener la antiguedad de la noticia: No se encontro el tag de titulo.")

        return antique

    def fetch_new_publish_date(self):
        """
        Convierte una cadena de texto que representa una fecha en diferentes formatos a una fecha estándar.
        
        La función maneja fechas en formato "d M Y" y cadenas relativas como "hace 3 días". También reemplaza
        los nombres de los meses en español por sus equivalentes en inglés para el correcto parseo de fechas.
        
        Returns:
            str: Fecha y hora en formato "dd-mm-YYYY HH:MM:SS".
        """
        # Si self.antique es None, no hacer nada y retornar None
        if self.antique is self.DEFAULT_VALUES['antique']:
            logger.error("No se puede obtener la antiguedad de la noticia sin el valor de")
            return self.DEFAULT_VALUES['antique']
        
        # Diccionario para reemplazar nombres de meses en español por inglés
        month_translations = {
            'ene': 'jan',
            'abr': 'apr',
            'ago': 'aug',
            'sept': 'sep',
            'dic': 'dec'
        }
        
        # Uso un valor local para no perder el original
        antique = self.antique
        
        # Reemplazar meses
        for es_month, en_month in month_translations.items():
            antique = antique.replace(es_month, en_month)
        
        # Validar si la cadena no contiene "hace" y parsear como fecha estándar
        if 'hace' not in antique:
            try:
                date_obj = datetime.strptime(antique, "%d %b %Y")
                date = date_obj.strftime("%d-%m-%Y")
                return f'{date} 12:00:00'
            except ValueError:
                logger.error("Error: La cadena de fecha no tiene el formato esperado")
                return None
        
        # Obtener el número y la unidad de tiempo de la cadena relativa
        try:
            parts = antique.split()
            if len(parts) < 3:
                raise ValueError("La cadena no contiene suficientes partes")
            cantidad = int(parts[1])
            unidad = parts[2]
        except (ValueError, IndexError) as e:
            logger.error(f"Error: {e}")
            return None
        
        # Obtener la fecha actual
        cdate = datetime.now()
        
        # Calcular la fecha de publicación restando la cantidad de tiempo adecuada
        try:
            if 'minuto' in unidad:
                date = cdate - timedelta(minutes=cantidad)
            elif 'hora' in unidad:
                date = cdate - timedelta(hours=cantidad)
            elif unidad in ['dia', 'dias', 'día', 'días']:
                date = cdate - timedelta(days=cantidad)
            elif 'semana' in unidad:
                date = cdate - timedelta(weeks=cantidad)
            elif 'mes' in unidad:
                date = cdate - timedelta(days=cantidad * 30)  # Suponiendo 30 días por mes
            elif 'año' in unidad:
                date = cdate - timedelta(days=cantidad * 365)  # Suponiendo 365 días por año
            else:
                raise ValueError(f"Unidad de tiempo [{unidad}] no reconocida")
        except ValueError as e:
            logger.error(f"Error: {e}")
            return None
        
        publish_date = '{} {}'.format(
            date.date().strftime("%d-%m-%Y"),
            date.time().strftime("%H:%M:%S")
        )
        
        return publish_date

def fetch_new_id(id_field='news_id', table_name='news', search_field='title', target='youtube.com'):
    with Database() as db:
        # Defino la consulta que tengo que realizar
        query = f"select {id_field} from {table_name} where {search_field} = '{target}'"

        # Obtengo el resultado de busqueda
        query_res = db.select(query)

        # Si obtengo un resultado lo proceso
        if ((query_res is not None) and
            (len(query_res) > 0)
        ):
            # El resultado es una lista de tuplas
            # Me quedo con el primer elemento
            result = [x[0] for x in db.select(query)]
            id = int(list(set(result))[0])

        # Si no se encuentra el ID obtengo uno nuevo
        else:
            query = f"select max({id_field}) from {table_name}"

            # El resultado es una lista de tuplas
            # Me quedo con el primer elemento
            result = [x[0] for x in db.select(query)]
            max_id = list(set(result))[0]

            # Ultimo check
            if max_id is None:
                id = 1
            else:
                # Genero el proximo ID
                id = int(max_id) + 1

    return id

if __name__ == "__main__":
    # Definir la categoría de productos
    topics = "juguetes"
    
    start_time = time.time()
    
    google_news_listings = GoogleNewsListings(topics)
    google_news_listings.fetch_data()
        
    end_time = time.time()
    execution_time = round( end_time - start_time, 3)
            
    logger.info(f'Tiempo de ejecucion: {execution_time} segundos.')
