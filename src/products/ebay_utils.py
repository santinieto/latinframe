import re
from unidecode import unidecode
from datetime import datetime, timedelta
import urllib.parse
import requests
from functools import partial
from multiprocessing import Pool, cpu_count
from bs4 import BeautifulSoup
import time

from src.utils.logger import Logger
from src.utils.utils import get_http_response
from src.products.product import Product

# Crear un logger
logger = Logger().get_logger()

# Define tu función de inicialización de cada objeto
def init_ebay_item(html_content):
    """
    Inicializa un objeto de la clase que corresponda.

    Args:
        html_content (str): Contenido HTML del cual extraer datos.

    Returns:
        El objeto del tipo correspondiente ya inicializado.
    """
    item = EbayProduct()
    item.set_html(html_content)
    item.fetch_data()
    return item

class EbayProductListings:
    ############################################################################
    # Atributos globables
    ############################################################################
    # Atributo de clase para almacenar la instancia única
    _instance = None
    
    ENABLE_MP = True
    N_CORES = -1
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
            self.n_cores = self.set_n_cores()
            
            # Defino una lista por defecto y
            # agrego las tematicas de interes
            self.add_topics(self.DEFAULT_TOPICS + topics)

            # Inicializar el objeto Pool para el procesamiento paralelo
            if self.ENABLE_MP:
                self.pool = Pool(processes=self.n_cores)
            else:
                self.pool = None
            
            self.initialized = True
    
    def set_n_cores(self):
        """
        Obtiene el número de procesos a utilizar según la configuración.
        """
        max_n_cores = cpu_count()
        if self.N_CORES < 0:
            return max_n_cores
        else:
            if self.N_CORES > max_n_cores:
                return max_n_cores
            else:
                return self.N_CORES

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
            url = f'https://www.ebay.com/sch/i.html?_from=R40&_nkw={encoded_topic}/'
            
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
                html_contents = html_content.find_all('li', class_=[
                        's-item',
                    ])
                
                #
                html_contents = html_contents[2:]
                
                if self.ENABLE_MP:
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
            init_func = partial(init_ebay_item)
            self.listings[topic]['items'] = self.pool.map(init_func, html_contents)
        except Exception as e:
            logger.error(f'Error al inicializar los objetos en paralelo. Error: {str(e)}')

    def serial_item_initialize(self, topic, html_contents):
        """
        Inicializa los objetos de forma serial.
        """
        try:
            self.listings[topic]['items'] = [init_ebay_item(x) for x in html_contents]
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

class EbayProduct(Product):
    def __init__(self, product_id=None, info_dict=None):
        # Actualiza los valores por defecto específicos de EbayProduct
        updated_defaults = {
            'currency': 'USD',
            'platform': 'Ebay'
        }
        
        # Combina los valores por defecto de Product con los específicos de EbayProduct
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
            logger.info(f"Los datos del producto {self.product_id} ya están cargados en el objeto EbayProduct.")
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
            
            logger.error(f"No se pudo cargar datos del producto {self.product_id} de Ebay usando metodos forzados.")
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
        logger.error(f"No se pudo cargar datos del producto {self.product_id} de Ebay.")
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
                
            if self.SAVE_HTML:
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
            # Busco el ID, como lo obtengo en Hexadecimal, lo paso a decimal
            match = self.html_content.get('id')
            if match:
                self.product_id = int( match.replace('item',''), 16)
                # Conformo la URL del producto
                self._fetch_product_url()
                # Termino la ejecucion de esta funcion
                return
            
            # Definir el patrón regex
            pattern = r'id="([^"]+)"'

            # Buscar el patrón en la cadena
            match = re.search(pattern, str(self.html_content))
            if match:
                self.product_id = int( match.group(1).replace('item',''), 16)
                # Conformo la URL del producto
                self._fetch_product_url()
                # Termino la ejecucion de esta funcion
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
        if self.product_id is None:
            logger.error(f"No se puede extraer la URL sin un ID de producto.")
            return
        
        try:
            self.url = f'https://www.ebay.com/itm/{self.product_id}'
            return
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
            # Obtengo la informacion del producto
            product_info = self.html_content.find('div', class_='s-item__info')
            
            # Intentar obtener el nombre del producto
            name_tag = product_info.find('div', class_='s-item__title')
            if name_tag:
                return name_tag.text
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
            # FIXME: No se como obtener esto
            ranking = self.DEFAULT_VALUES['ranking']
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
            # Obtengo la informacion del producto
            product_info = self.html_content.find('div', class_='s-item__info')
            # Obtener el precio del producto
            price_tag = product_info.find('span', class_='s-item__price').text
            if price_tag:
                price, _ = self.get_product_price_currency(price_tag)
        except AttributeError:
            logger.error("No se pudo obtener el precio del producto: no se encontró la etiqueta de precio.")
        except ValueError:
            logger.error("No se pudo convertir el precio del producto a un número válido.")

        return price
    
    def get_product_price_currency(self, price_string):
        """
        Calcula el promedio de dos precios en una cadena o devuelve el precio único si solo hay uno.
        
        Parámetros:
        price_string (str): Cadena que contiene uno o dos precios con la moneda.

        Retorna:
        tuple: El promedio de los precios o el precio único, formateado con la moneda.
            En caso de error, devuelve (None, None).
        """
        try:
            # Reemplazar caracteres no deseados (como \xa0) y comas por puntos decimales
            clean_string = price_string.replace('\xa0', '').replace(',', '.')

            # Extraer los números de la cadena
            numbers = re.findall(r'\d+\.\d+', clean_string)

            if not numbers:
                raise ValueError("No se encontraron precios en la cadena proporcionada.")

            # Convertir los números a valores decimales
            decimal_numbers = [float(number) for number in numbers]

            # Extraer la moneda de la cadena
            currency_matches = re.findall(r'[A-Z]+', clean_string)
            if not currency_matches:
                raise ValueError("No se encontró la moneda en la cadena proporcionada.")
            currency = currency_matches[0]
            
            # Convertir el signo de dólares
            if currency in ['U$S','US$','U$D']:
                currency = 'USD'

            # Calcular el promedio o devolver el único precio
            if len(numbers) == 1:
                # Si solo hay un número, usar ese número como promedio
                average_price = decimal_numbers[0]
            else:
                # Si hay dos números, calcular el promedio
                average_price = sum(decimal_numbers) / len(decimal_numbers)
                average_price = round(average_price, 3)
            
            return average_price, currency
        except ValueError as e:
            logger.error(f"Error de valor al intentar obtener el precio o moneda del producto {self.product_id}. Error: {e}.")
        except IndexError as e:
            logger.error("Error de índice: No se pudo encontrar la moneda en la cadena del producto {self.product_id}. Error: {e}.")
        except Exception as e:
            logger.error(f"Error inesperado al intentar obtener el precio o moneda del producto {self.product_id}. Error: {e}.")
        
        return 0.0, self.DEFAULT_VALUES['currency']

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
            # FIXME: No se como obtener esto
            cuotas = self.DEFAULT_VALUES['installments']
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
            # Obtengo la informacion del proucto
            product_info = self.html_content.find('div', class_='s-item__info')
            store_tag = product_info.find('span', class_='s-item__itemLocation')
            if store_tag:
                store = store_tag.text.replace('de ','')
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
            # FIXME: No se como obtener esto
            rating = self.DEFAULT_VALUES['rating']
        except AttributeError:
            logger.error("No se pudo obtener la calificación del producto: no se encontró la etiqueta de calificación.")
        
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
            # FIXME: No se como obtener esto
            rating_count = self.DEFAULT_VALUES['rating_count']
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
            # Obtengo la informacion del producto
            product_info = self.html_content.find('div', class_='s-item__info')
            is_best_seller_tag = product_info.find('div', class_='s-item__details-section--secondary')
            if is_best_seller_tag:
                is_best_seller = bool( is_best_seller_tag )
            else:
                is_best_seller = bool( 0 )
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
            # Obtengo la informacion del producto
            product_info = self.html_content.find('div', class_='s-item__info')
            is_promoted = 'kexu191' in product_info.find('span', class_='s-item__sep').find('span').get('style')
        except AttributeError:
            logger.error("No se pudo obtener información sobre si el producto está promocionado: no se encontró la etiqueta correspondiente.")

        return is_promoted

    def _fetch_product_currency(self):
        """
        Obtiene el símbolo de la moneda del contenido HTML.
        Si no se puede obtener, se establece como '-'.
        """
        # Verificar si hay contenido HTML disponible
        if self.html_content is None:
            logger.error("No se puede obtener el símbolo de la moneda sin contenido HTML.")
            return self.DEFAULT_VALUES['currency_symbol']
        
        try:
            # Obtengo la informacion del producto
            product_info = self.html_content.find('div', class_='s-item__info')
            # Obtener el precio del producto
            price_tag = product_info.find('span', class_='s-item__price').text
            if price_tag:
                _, currency_symbol = self.get_product_price_currency(price_tag)
            else:
                currency_symbol = '-'
        except AttributeError:
            logger.error("No se pudo obtener el símbolo de la moneda: no se encontró la etiqueta correspondiente.")
            currency_symbol = '-'

        return currency_symbol

if __name__ == "__main__":
    # Definir la categoría de productos
    topics = "juguetes"
    
    start_time = time.time()
    
    ebay_listings = EbayProductListings(topics)
    ebay_listings.fetch_data()
    ebay_listings.show_items_content()
        
    end_time = time.time()
    execution_time = round( end_time - start_time, 3)
            
    logger.info(f'Tiempo de ejecucion: {execution_time} segundos.')