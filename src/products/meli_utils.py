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
from datetime import datetime, timedelta

# Imports locales
from src.logger.logger import Logger
from src.utils.utils import get_http_response, getenv
from src.products.product import Product

################################################################################
# Genero una instancia del Logger
################################################################################
logger = Logger(os.path.basename(__file__)).get_logger()

# Define tu función de inicialización de cada objeto
def init_alibaba_item(html_content):
    """
    Inicializa un objeto de la clase que corresponda.

    Args:
        html_content (str): Contenido HTML del cual extraer datos.

    Returns:
        El objeto del tipo correspondiente ya inicializado.
    """
    item = MeLiProduct()
    item.set_html(html_content)
    item.fetch_data()
    return item

class MeLiProductListings:
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
            self.save_html = getenv('PRODUCTS_SAVE_HTML', self.DEFAULT_SAVE_HTML)
            self.enable_mp = getenv('ENABLE_MP', self.DEFAULT_ENABLE_MP)
            self.n_cores = self.set_n_cores()
            
            # Defino una lista por defecto y
            # agrego las tematicas de interes
            self.add_topics(self.DEFAULT_TOPICS + topics)

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
            url = f'https://listado.mercadolibre.com.ar/{encoded_topic}/'
            
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
                
                try:
                    # Obtengo los items encontrados
                    # NOTA: Aca es donde hay que cambiar para aplicar el filtro correcto
                    html_contents = html_content.find_all('div', class_='ui-search-result__wrapper')
                    
                    if self.enable_mp:
                        # Procesamiento en paralelo
                        self.parallel_item_initialize(topic, html_contents)
                    else:
                        # Procesamiento en serie
                        self.serial_item_initialize(topic, html_contents)
                        
                    # Le asigno la tematica correspondientea cada item
                    for item in self.listings[topic]['items']:
                        item.topic = topic
                except Exception as e:
                    logger.error(f"Error al buscar los productos para la tematica [{topic}]. Error: {e}.")
                
            else:
                logger.error(f"El contenido HTML para la tematica [{topic}] es None, no se pueden buscar informacion.")

    def parallel_item_initialize(self, topic, html_contents):
        """
        Inicializa los objetos utilizando multiprocessing.Pool.
        """
        try:
            # Paso el contenido a string porque sino, no puede procesar en paralelo
            html_contents = [str(x) for x in html_contents]
            init_func = partial(init_alibaba_item)
            self.listings[topic]['items'] = self.pool.map(init_func, html_contents)
        except Exception as e:
            logger.error(f'Error al inicializar los objetos en paralelo. Error: {str(e)}')

    def serial_item_initialize(self, topic, html_contents):
        """
        Inicializa los objetos de forma serial.
        """
        try:
            self.listings[topic]['items'] = [init_alibaba_item(str(html_content)) for html_content in html_contents]
        except Exception as e:
            logger.error(f'Error al inicializar los objetos en serie. Error: {str(e)}')

    def show_items_content(self):
        """
        Muestra el contenido de cada item para cada tematica.
        """
        for topic, listing in self.listings.items():
            products = listing.get('items')
            if products:
                logger.info(f"Contenido de las noticias para la tematica [{topic}]:")
                for product in products:
                    logger.info(str(product))
            else:
                logger.info(f"No se encontraron noticias en el objeto GoogleNewsListing para la temática {topic}.")

    def get_items(self):
        """
        Devuelvo una lista con todos los items disponibles.
        """
        tot_items = []
        for _, listing in self.listings.items():
            items = listing.get('items')
            if items:
                tot_items = tot_items + items
            else:
                topic = listing.get('topic')
                logger.warning(f'No se obtuvieron productos para la tematica [{topic}]')
        return tot_items

    def fetch_data(self):
        """
        Funcion principal de ejecucion.
        """
        self.generate_urls()
        self.fetch_html_content()
        self.find_items()
        # self.show_items_content()
        
        return self.get_items()

class MeLiProduct(Product):
    def __init__(self, product_id=None, info_dict=None):
        # Actualiza los valores por defecto específicos de MeLiProduct
        updated_defaults = {
            'currency': 'ARS',
            'platform': 'Mercado Libre'
        }
        
        # Combina los valores por defecto de Product con los específicos de MeLiProduct
        if info_dict:
            info_dict = {**updated_defaults, **info_dict}
        else:
            info_dict = updated_defaults
        
        # Inicializa la clase base con los valores combinados
        super().__init__(product_id, info_dict)
        self.data_loaded = False
        
    def set_html(self, html_content):
        """
        Establece el contenido HTML del producto.

        Args:
            html_content (str): Contenido HTML a establecer.
        """
        if isinstance(html_content, str):
            html_content = BeautifulSoup(html_content, 'html.parser')
        self.html_content = html_content
        
        if self.product_id is None:
            self._fetch_product_id()
            
        if self.product_id:
            if self.DEBUG:
                logger.info(f"Contenido HTML establecido con éxito para el producto {self.product_id}.")
        else:
            self.html_content = None
            logger.error(f"No se establecio el contenido HTML para el producto dado que no se encontro el ID.\n\nHTML\n\n{html_content}")

    ############################################################################
    # Actualizar los datos del producto
    ############################################################################
    def fetch_data(self, info_dict=None, force_method=None):
        """
        Intenta cargar datos del producto utilizando diferentes métodos.

        El orden de preferencia para cargar los datos es el siguiente:
        1. Datos proporcionados durante la inicialización del objeto.
        2. Utilización de alguna API.
        3. Scraping de contenido HTML.

        Si alguno de los métodos falla, se pasará automáticamente al siguiente método.

        Args:
            info_dict (dict): Diccionario con datos del producto para cargar.
            force_method (str): Método para forzar la carga de datos ('api' para la utilizacion de una API, 'html' para scraping HTML).

        Returns:
            bool: True si se cargaron los datos con éxito, False en caso contrario.
        """
        # Verifica si los datos ya están cargados
        if self.data_loaded:
            logger.info(f"Los datos del producto {self.product_id} ya están cargados en el objeto MeLiProduct.")
            self.fetch_status = True
            return

        # Intenta cargar datos del diccionario proporcionado durante la inicialización
        if info_dict:
            self.load_from_dict(info_dict)
            logger.info(f"Los datos del producto {self.product_id} se cargaron exitosamente desde el diccionario proporcionado durante la inicialización.")
            self.fetch_status = True
            return

        # Verifica si se especificó un método forzado
        if force_method:
            logger.info(f"Los datos del producto {self.product_id} se van a cargar forzadamente usando el metodo {force_method}.")
            
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
            
            logger.error(f"No se pudo cargar datos del producto {self.product_id} de Mercado Libre usando metodos forzados.")
            self.fetch_status = False
            return

        # Intenta cargar datos utilizando la API de Mercado Libre si no se especifica un método forzado
        if self._load_data_from_api():
            self.fetch_status = True
            return

        # Intenta cargar datos mediante scraping de contenido HTML si no se especifica un método forzado
        if self._load_data_from_html():
            self.fetch_status = True
            return

        # Si no se pudo cargar datos de ninguna manera, registra un mensaje de error
        logger.error(f"No se pudo cargar datos del producto {self.product_id} de Mercado Libre.")
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
                
            # Si hubo un fallo al obtener el codigo HTML del producto, logeo un
            # error y salgo de la funcion
            if self.html_content in [False, None]:
                logger.error(f"No se dispone de contenido HTML para el producto {self.product_id}.")
                return False
                
            if self.save_html:
                self.save_html_content()
            
            # Crear el diccionario para los datos
            product_data = {
                'product_id': self.product_id, # Tiene que estar siempre este campo
                'url': self.url,
                'product_name': self._fetch_product_name(),
                'ranking': self._fetch_product_ranking(),
                'price': self._fetch_product_price(),
                'store': self._fetch_product_store(),
                'installments': self._fetch_product_installments(),
                'rating': self._fetch_product_rating(),
                'rating_count': self._fetch_product_rating_count(),
                'is_best_seller': self._fetch_product_best_seller(),
                'is_promoted': self._fetch_product_promoted(),
                'currency': self._fetch_product_currency(),
                }
            
            # Actualiza la información del producto con los datos obtenidos del scraping
            self.load_from_dict(product_data)
            
            # Mensaje de debug
            if self.DEBUG:
                logger.info("Los datos se cargaron exitosamente mediante scraping de contenido HTML.")
            return True
        
        except Exception as e:
            logger.warning(f"Fallo al cargar datos mediante scraping de contenido HTML: {e}")

        return False

    def _fetch_product_id(self):
        """
        Intenta extraer el ID del producto de la URL o del contenido HTML.
        Si no puede extraerlo, establece el ID del producto como None y registra un error.
        """
        try:
            # Intento buscar por la URL
            self._fetch_product_url()
            if self.url:
                # Busco el ID
                match = re.search(r"MLA\d+", self.url)
                if match:
                    self.product_id = match.group(0)
                    return
                match = re.search(r"MLA-\d+", self.url)
                if match:
                    self.product_id = match.group(0).replace('-', '')
                    return
            
            if self.url:
                logger.warning(f'No se encontró el ID del producto en la URL: [{self.url}]. Se van a usar otros métodos que pueden NO ser exactos.')
            else:
                logger.warning(f'No se encontro la URL del producto en el contenido HTML:\n\n{self.html_content}')

            # Si llegamos aquí, no se encontró un ID de producto en la URL
            # Intentar con otros métodos si hay contenido HTML
            if self.html_content:
                # Intento buscar un elemento input con name='itemId'
                elem = self.html_content.find('input', {'name': 'itemId'})
                if elem:
                    self.product_id = elem.get('value')
                    return
                
                # Intento buscar un formulario y extraer el ID de la acción
                elem = self.html_content.find('form')
                if elem:
                    self.product_id = elem.get('action').split('/')[-1]
                    return
            
            # Si no se pudo encontrar el ID del producto, establecer como None
            self.product_id = None
            logger.error("No se pudo extraer el ID del producto de la URL o del contenido HTML.")
        except AttributeError:
            # Si se produce un error de atributo (por ejemplo, el método find() devuelve None), registrar el error y establecer el ID del producto como None
            self.product_id = None
            logger.error("No se encontraron elementos coincidentes en el contenido HTML para extraer el ID del producto.")
        except Exception as e:
            # Si ocurre algún error inesperado, registrar el error y establecer el ID del producto como None
            self.product_id = None
            logger.error(f"Error al intentar extraer el ID del producto: {e}")
            
    def _fetch_product_url(self):
        """
        Extrae la URL del contenido HTML.
        Retorna la URL si se encuentra, de lo contrario, retorna None.
        """
        # Comprobación de casos especiales
        if self.url:
            logger.warning(f"El producto ya tiene cargada una dirección URL: {self.url}")
            return
        if self.html_content is None:
            logger.error(f"No se puede extraer la URL sin contenido HTML.")
            return
        
        try:
            classes = [
                'ui-search-item__group__element',
                'ui-search-link__title-card',
                'ui-search-link'
            ]
            for xclass in classes:
                elem = self.html_content.find('a', class_=xclass)
                if elem:
                    self.url = elem.get('href')
                    return
        except AttributeError:
            logger.error(f"Error al buscar la URL en el contenido HTML: No se encontró el atributo '{xclass}'.")
        except Exception as e:
            logger.error(f"Error al buscar la URL en el contenido HTML. Error: {e}")
    
        # Si no se encontró la URL, registramos un error
        logger.error("No se pudo encontrar la URL en el contenido HTML.")
        self.url = self.DEFAULT_VALUES['url']

    def _fetch_product_name(self):
        """
        Obtiene el nombre del producto del contenido HTML.
        Si no se puede obtener, establece el nombre como 'Unknown toy'.
        """
        # Verificar si hay contenido HTML disponible
        if self.html_content is None:
            logger.error("No se puede obtener el nombre del producto sin contenido HTML.")
            return self.DEFAULT_VALUES['product_name']
        
        try:
            # Intentar obtener el nombre del producto
            name_tag = self.html_content.find('h2', class_='ui-search-item__title')
            if name_tag:
                return name_tag.text.strip()
            else:
                logger.warning("No se encontró ninguna etiqueta de nombre para el producto.")
                return self.DEFAULT_VALUES['product_name']
        except Exception as e:
            # Si hay algún error, establecer el nombre por defecto y registrar el error
            logger.error(f"Error al obtener el nombre del producto {self.product_id}. Error: {e}")
            return self.DEFAULT_VALUES['product_name']

    def _fetch_product_ranking(self):
        """
        Obtiene el ranking del producto de la URL.
        Si no se puede obtener, se establece como 0.
        """
        # Verificar si hay URL disponible
        if self.url is None:
            logger.error("No se puede obtener el ranking del producto sin una URL.")
            return self.DEFAULT_VALUES['ranking']
        
        ranking = self.DEFAULT_VALUES['ranking']
        
        try:
            # Buscar el ranking en la URL
            match = re.search(r'position=(\d+)', self.url)
            if match:
                ranking = int(match.group(1))
        except Exception as e:
            logger.error(f"Error al obtener el ranking del producto: {e}")

        return ranking

    def _fetch_product_price(self):
        """
        Obtiene el precio del producto del contenido HTML.
        Si no se puede obtener el precio, se devuelve como 0.
        """
        # Verificar si hay contenido HTML disponible
        if self.html_content is None:
            logger.error("No se puede obtener el nombre del producto sin contenido HTML.")
            return self.DEFAULT_VALUES['price']
        
        # Inicializar valor predeterminado
        price = self.DEFAULT_VALUES['price']

        try:
            # Obtener el precio del producto
            price_tag = self.html_content.find('span', class_=[
                'price-tag-fraction',
                'andes-money-amount__fraction',
            ])
            if price_tag:
                price = float(price_tag.get_text().replace('.', '').replace(',', '.'))
        except AttributeError:
            logger.error("No se pudo obtener el precio del producto: no se encontró la etiqueta de precio.")
        except ValueError:
            logger.error("No se pudo convertir el precio del producto a un número válido.")

        return price

    def _fetch_product_installments(self):
        """
        Obtiene el número de cuotas del producto del contenido HTML.
        Si no se puede obtener el número de cuotas, se devuelve como 1.
        """
        # Verificar si hay contenido HTML disponible
        if self.html_content is None:
            logger.error("No se puede obtener el nombre del producto sin contenido HTML.")
            return self.DEFAULT_VALUES['installments']
        
        # Inicializar valor predeterminado
        cuotas = self.DEFAULT_VALUES['installments']

        try:
            # Obtener el número de cuotas del producto
            installments_tag = self.html_content.find(
                ['div','span'], class_=['ui-search-installments']
                )
            if installments_tag:
                cuotas = installments_tag.get_text()
        except AttributeError:
            logger.error("No se pudo obtener el número de cuotas del producto: no se encontró la etiqueta de cuotas.")
        except (ValueError, IndexError):
            logger.error("No se pudo convertir el número de cuotas del producto a un número entero válido.")
            logger.warning(self.html_content)
        return cuotas
    
    def _fetch_product_store(self):
        """
        Obtiene el vendedor del producto del contenido HTML.
        Si no se puede obtener, se establece como '-'.
        """
        # Verificar si hay contenido HTML disponible
        if self.html_content is None:
            logger.error("No se puede obtener el nombre del producto sin contenido HTML.")
            return self.DEFAULT_VALUES['store']
        
        # Inicializar valor predeterminado
        store = self.DEFAULT_VALUES['store']
        
        try:
            store_tag = self.html_content.find('p', class_='ui-search-official-store-label')
            if store_tag:
                store = re.sub(r'(?i)por ', '', store_tag.text)
        except AttributeError:
            logger.error("No se pudo obtener el vendedor del producto: no se encontró la etiqueta de tienda.")

        return store
    
    def _fetch_product_rating(self):
        """
        Obtiene la calificación del producto del contenido HTML.
        Si no se puede obtener, se establece como 'Unknown'.
        """
        # Verificar si hay contenido HTML disponible
        if self.html_content is None:
            logger.error("No se puede obtener la calificación del producto sin contenido HTML.")
            return self.DEFAULT_VALUES['rating'], self.DEFAULT_VALUES['rate_count']
        
        # Inicializar valores predeterminados
        rating = self.DEFAULT_VALUES['rating']
        
        try:
            rate_box = self.html_content.find('span', class_=[
                'ui-search-reviews__ratings',
                'ui-pdp-review__ratings'
            ])
            full_stars = len(rate_box.find_all('svg', class_=[
                'ui-search-icon--star-full',
                'ui-pdp-icon--star-full'
            ]))
            half_stars = len(rate_box.find_all('svg', class_=[
                'ui-search-icon--star-half',
                'ui-pdp-icon--star-half'
            ]))
            rating = full_stars + half_stars * 0.5
        except AttributeError:
            logger.warning(f"No se pudo obtener la calificación del producto [{self.product_id}]: no se encontró la etiqueta de calificación. URL: [{self.url}]")
        
        return rating

    def _fetch_product_rating_count(self):
        """
        Obtiene el número de calificaciones del producto del contenido HTML.
        Si no se puede obtener, se establece como '-'.
        """
        # Verificar si hay contenido HTML disponible
        if self.html_content is None:
            logger.error("No se puede obtener el número de calificaciones del producto sin contenido HTML.")
            return self.DEFAULT_VALUES['rating_count']
        
        # Inicializar valor predeterminado
        rating_count = self.DEFAULT_VALUES['rating_count']
        
        try:
            rate_count_tag = self.html_content.find('span', class_='ui-search-reviews__amount')
            if rate_count_tag:
                rating_count = int(rate_count_tag.text[1:-1])
        except (AttributeError, ValueError):
            logger.error("No se pudo obtener el número de calificaciones del producto.")
        
        return rating_count

    def _fetch_product_best_seller(self):
        """
        Obtiene datos sobre si el producto es el más vendido del contenido HTML.
        Si no se puede obtener, se establece como 0.
        """
        # Verificar si hay contenido HTML disponible
        if self.html_content is None:
            logger.error("No se puede obtener información sobre si el producto es el más vendido sin contenido HTML.")
            return self.DEFAULT_VALUES['most_selled']
        
        is_best_seller = self.DEFAULT_VALUES['is_best_seller']
        
        try:
            if self.html_content.find('div', class_='ui-search-item__highlight-label__container') is not None:
                is_best_seller = 1
        except AttributeError:
            logger.error("No se pudo obtener información sobre si el producto es el más vendido: no se encontró la etiqueta correspondiente.")
        
        return is_best_seller
        
    def _fetch_product_promoted(self):
        """
        Obtiene datos sobre si el producto está promocionado del contenido HTML.
        Si no se puede obtener, se establece como 0.
        """
        # Verificar si hay contenido HTML disponible
        if self.html_content is None:
            logger.error("No se puede obtener información sobre si el producto está promocionado sin contenido HTML.")
            return self.DEFAULT_VALUES['is_promoted']
        
        is_promoted = self.DEFAULT_VALUES['is_promoted']
        
        try:
            if self.html_content.find('span', class_='ui-search-item__pub-label ui-search-item__pub-label--blue') is not None:
                is_promoted = 1
        except AttributeError:
            logger.error("No se pudo obtener información sobre si el producto está promocionado: no se encontró la etiqueta correspondiente.")

        return is_promoted

    def _fetch_product_currency(self):
        """
        Determina la moneda basándose en el símbolo de moneda y la URL.
        """
        # Verificar si hay contenido HTML disponible
        if self.html_content is None:
            logger.error("No se puede determinar la moneda sin contenido HTML.")
            return self.DEFAULT_VALUES['currency']
        
        # Obtener el símbolo de la moneda
        currency_symbol = self._fetch_product_currency_symbol()
        
        # Obtener la URL
        url = self.url
        
        # Determinar la moneda
        if currency_symbol == '$':
            if '.mx' in url:
                return 'MXN'
            elif '.ar' in url:
                return 'ARS'
        elif currency_symbol in ['U$S','US$','U$D']:
                return 'USD'
        elif currency_symbol == '₱':
            if '.mx' in url:
                return 'MXN'
            else:
                return 'PHP'
        elif currency_symbol == 'R$':
            return 'BRL'
        else:
            return 'UNKNOWN'

    def _fetch_product_currency_symbol(self):
        """
        Obtiene el símbolo de la moneda del contenido HTML.
        Si no se puede obtener, se establece como '-'.
        """
        # Verificar si hay contenido HTML disponible
        if self.html_content is None:
            logger.error("No se puede obtener el símbolo de la moneda sin contenido HTML.")
            return self.DEFAULT_VALUES['currency_symbol']
        
        try:
            symbol_tag = self.html_content.find('span', class_='andes-money-amount__currency-symbol')
            if symbol_tag:
                currency_symbol = symbol_tag.text.strip()
            else:
                currency_symbol = '-'
        except AttributeError:
            logger.error("No se pudo obtener el símbolo de la moneda: no se encontró la etiqueta correspondiente.")
            currency_symbol = '-'

        return currency_symbol

if __name__ == "__main__":
    # Definir la categoría de productos
    topics = "productos"
    
    start_time = time.time()
    
    meli_listings = MeLiProductListings(topics)
    meli_listings.fetch_data()
    meli_listings.show_items_content()
        
    end_time = time.time()
    execution_time = round( end_time - start_time, 3)
            
    logger.info(f'Tiempo de ejecucion: {execution_time} segundos.')