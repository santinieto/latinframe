# Imports estándar de Python
import os
# import sys

# Añade el directorio raíz del proyecto a sys.path
# current_path = os.path.dirname(os.path.abspath(__file__))
# project_root = os.path.abspath(os.path.join(current_path, '..', '..'))  # Ajusta según la estructura de tu proyecto
# sys.path.append(project_root)

# Imports de terceros
from multiprocessing import cpu_count
import time

# Imports locales
from src.logger.logger import Logger
from src.database.db import Database
from src.products.meli_utils import MeLiProductListings
from src.products.ebay_utils import EbayProductListings
from src.products.alibaba_utils import AlibabaProductListings
from src.utils.utils import getenv

################################################################################
# Genero una instancia del Logger
################################################################################
logger = Logger(os.path.basename(__file__)).get_logger()
    
################################################################################
# Gestionador de argumentos
################################################################################
def handle_products_args(args):
    """
    Gestiona los argumentos proporcionados para obtener productos.

    :param args: Argumentos procesados de la línea de comandos.
    """
    # Defino un nombre por defecto al modulo
    module_name = 'Gestionador de productos'

    # Creo el objeto unico que gestiona los productos
    product_manager = ProductManager(args.topics)

    # Muestro el mensaje de ayuda
    if args.help:
        logger.info(show_help_message(module_name))
        return

    # Lista de funciones para obtener productos
    fetch_functions = {
        'all': product_manager.fetch_products,
        'mercadolibre': product_manager.fetch_meli_products,
        'ebay': product_manager.fetch_ebay_products,
        'alibaba': product_manager.fetch_alibaba_products
    }

    # Variable para verificar si se ha llamado a alguna función de fetch
    called_fetch = False

    for arg, fetch_function in fetch_functions.items():
        if getattr(args, arg, False):
            fetch_function()
            called_fetch = True

    if called_fetch:
        # Muestro la informacion
        product_manager.show_items()
        # Guardo los resultados en la base de datos
        product_manager.insert_data_to_db()
    else:
        # Mensaje de error por defecto si no se especifica una fuente válida
        logger.info(show_help_message(module_name))

def show_help_message(module_name):
    """
    Muestra el mensaje de ayuda detallado.
    """
    help_message = f"""
    {module_name} - Opciones disponibles:
    
    --help            : Mostrar este mensaje de ayuda.
    --all             : Obtener productos de todas las páginas.
    --mercadolibre    : Hacer un scrap de Mercado Libre.
    --ebay            : Hacer un scrap de eBay.
    --alibaba         : Hacer un scrap de Alibaba.
    --topics TOPICS   : Temas para la búsqueda de productos (puede aceptar múltiples temas separados por espacios).
    """
    return help_message

################################################################################
# Clase principal
################################################################################
class ProductManager:
    ############################################################################
    # Atributos globables
    ############################################################################
    # Atributo de clase para almacenar la instancia única
    _instance = None

    # Configuraciones por defecto
    DEFAULT_MELI_FETCH = True
    DEFAULT_ALIBABA_FETCH = True
    DEFAULT_EBAY_FETCH = True
    DEFAULT_ADD_CHANNEL_NAMES = False
    DEFAULT_N_PRODUCTS_FETCH = 10
    DEFAULT_N_CORES = -1
    DEFAULT_DB_NAME = 'latinframe.db'
    DEBUG = True
    
    DEFAULT_TOPICS = [
        'juguetes',
        # 'disney',
        # 'pixar',
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
        # Evitar la inicialización múltiple
        # verificando si existe el atributo initialized en la clase
        if not hasattr(self, 'initialized'):
            self.topics = []
            self.items = []
            
            self.meli_fetch = getenv('PRODUCTS_MELI_FETCH', self.DEFAULT_MELI_FETCH )
            self.alibaba_fetch = getenv('PRODUCTS_ALIBABA_FETCH', self.DEFAULT_ALIBABA_FETCH )
            self.ebay_fetch = getenv('PRODUCTS_EBAY_FETCH', self.DEFAULT_EBAY_FETCH )
            self.add_channel_names = getenv('PRODUCTS_ADD_CHANNEL_NAMES', self.DEFAULT_ADD_CHANNEL_NAMES )
            self.n_products_fetch = getenv('PRODUCTS_N_PRODUCTS_FETCH', self.DEFAULT_N_PRODUCTS_FETCH )
            self.db_name = getenv('DB_NAME', self.DEFAULT_DB_NAME)
            self.n_cores = self.set_n_cores()
            
            # Defino una lista por defecto y
            # agrego las tematicas de interes
            self.add_topics(self.DEFAULT_TOPICS + topics)

            # Inicializar la base de datos
            self.database = self.initialize_database()
            
            # Obtengo los nombres de los canales desde la base de datos
            if self.add_channel_names:
                self.load_channel_names_from_database()
            
            # Marco la clase como inicializada
            self.initialized = True
            
            # Muestro los datos si fuera necesario
            if self.DEBUG:
                logger.info(str(self))
    
    def __str__(self):
        """
        Devuelve una representación de cadena con los datos relevantes de la clase.
        """
        info_str = (
            f"- Obtencion de productos desde Mercado Libre: {self.meli_fetch}\n"
            f"- Obtencion de productos desde Ebay: {self.ebay_fetch}\n"
            f"- Obtencion de productos desde Alibaba: {self.alibaba_fetch}\n"
            f"- Nombre de la base de datos: {self.db_name}\n"
            f"- Tematicas a buscar: {self.topics}\n"
            f"- Product Manager listo para operar: {self.initialized}"
        )
        return info_str
    
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

    def initialize_database(self):
        """
        Inicializa la base de datos.
        """
        try:
            # Crear una instancia de Database y abrir la base de datos
            return Database(self.db_name)
        except Exception as e:
            # Manejar el error al abrir la base de datos
            logger.error(f'Error al inicializar la base de datos. Error: {e}.')
            return None
        
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

    ############################################################################
    # Obtencion de productos
    ############################################################################
    def fetch_meli_products(self):
        self.items = self.items + MeLiProductListings(self.topics).fetch_data()
    
    def fetch_alibaba_products(self):
        self.items = self.items + AlibabaProductListings(self.topics).fetch_data()
    
    def fetch_ebay_products(self):
        self.items = self.items + EbayProductListings(self.topics).fetch_data()
        
    def fetch_products(self):
        self.items = []
        
        if self.meli_fetch:
            self.fetch_meli_products()
            
        if self.alibaba_fetch:
            self.fetch_alibaba_products()
            
        if self.ebay_fetch:
            self.fetch_ebay_products()
        
    def show_items(self):
        """
        Muestra el contenido de cada item.
        """
        for item in self.items:
            logger.info(str(item))
                
    ############################################################################
    # Interacciones con la base de datos
    ############################################################################
    def load_channel_names_from_database(self):
        """
        Carga los canales de YouTube desde la base de datos y los agrega a la
        lista tematicas a buscar.
        """
        if not self.database:
            logger.error("La base de datos no está inicializada.")
            return

        try:
            # Obtener los IDs de los canales de la base de datos
            channel_names_from_db = self.database.get_youtube_channel_data(target='CHANNEL_NAME', sort='asc')
            self.add_topics(channel_names_from_db)
        except Exception as e:
            logger.error(f"Error al cargar los canales desde la base de datos. Error: {e}.")
    
    def insert_data_to_db(self):
        """
        Inserta los datos obtenidos desde los sitios de compra en la base de datos.
        """
        # try:
        # Inserto los datos de los productos que se obtuvieron con exito
        for item in self.items:
            if item.fetch_status:
                self.database.insert_product_record( item.to_dicc() )
        # except Exception as e:
        #     logger.error(f"Error al insertar datos para los productos en la base de datos: {str(e)}")
    
if __name__ == "__main__":
    import argparse
    
    # Arranco la cuenta de tiempo
    start_time = time.time()
    
    # Configuración del parser de argumentos
    parser = argparse.ArgumentParser(description='Gestionador de productos', add_help=False)

    # Definición de los argumentos aceptados por el script
    parser.add_argument('--help', action='store_true', help='Mostrar mensaje de ayuda')
    parser.add_argument('--all', action='store_true', help='Obtener productos de todas las páginas')
    parser.add_argument('--mercadolibre', action='store_true', help='Hacer un scrap de Mercado Libre')
    parser.add_argument('--ebay', action='store_true', help='Hacer un scrap de eBay')
    parser.add_argument('--alibaba', action='store_true', help='Hacer un scrap de Alibaba')
    parser.add_argument('--topics', type=str, nargs='+', default=[], help='Temas para la búsqueda de productos')

    # Análisis de los argumentos de la línea de comandos
    args = parser.parse_args()

    # Llamada a la función para gestionar los argumentos
    handle_products_args(args)
        
    # Detengo la cuenta de tiempo y muestro el resultado
    end_time = time.time()
    execution_time = round( end_time - start_time, 3)
    logger.info(f'Tiempo de ejecucion: {execution_time} segundos.')