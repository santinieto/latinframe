from multiprocessing import cpu_count
import time
import os

from src.logger.logger import Logger
from src.database.db import Database
from src.utils.driver import Driver
from src.utils.utils import SIMILARWEB_BASE_URL
from src.utils.utils import get_similarweb_url_tuple, getenv
from src.similarweb.similarweb import SimilarWebTopWebsitesTable
from src.similarweb.similarweb import SimilarWebWebsite
    
################################################################################
# Crear un logger
################################################################################
logger = Logger(os.path.basename(__file__)).get_logger()

################################################################################
# Clase principal
################################################################################
class SimilarWebManager:
    ############################################################################
    # Atributos globables
    ############################################################################
    # Atributo de clase para almacenar la instancia única
    _instance = None

    # Configuraciones por defecto
    DEFAULT_DEFAULT_N_WEBS_FETCH = 10
    DEFAULT_SKIP_SCRAP = False
    DEFAULT_N_CORES = 4
    DEFAULT_DB_NAME = 'latinframe.db'
    DEFAULT_DELAY = 8
    DEBUG = True
    RESULTS_PATH = r'results/similarweb/'

    ############################################################################
    # Metodos de incializacion
    ############################################################################
    # Cuando solicito crear una instancia me aseguro que
    # si ya hay una creada, devuelvo esa misma
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, domains=[]):
        # Evitar la inicialización múltiple
        # verificando si existe el atributo initialized en la clase
        if not hasattr(self, 'initialized'):
            self.domains = domains
            self.results_path = self.RESULTS_PATH
            
            self.n_webs_fetch = getenv('SIMILARWEB_N_WEBS_FETCH', self.DEFAULT_DEFAULT_N_WEBS_FETCH)
            self.skip_scrap = getenv('SIMILARWEB_SKIP_SCRAP', self.DEFAULT_SKIP_SCRAP)
            self.db_name = getenv('DB_NAME', self.DEFAULT_DB_NAME)
            self.delay = getenv('SIMILARWEB_DELAY', self.DEFAULT_DELAY)
        
            # Comprobaciones de seguridad
            self.n_webs_fetch = max(self.n_webs_fetch, 0) # Me aseguro que no sea menor que 0
            
            # Obtengo la cantidad de sitios a scrapear al mismo tiempo
            self.n_cores = self.set_n_cores()

            # Inicializar la base de datos
            self.database = self.initialize_database()

            # Inicializar el driver
            self.driver = self.initialize_driver()
            
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
            f"- Nombre de la base de datos: {self.db_name}\n"
            f"- SimilarWeb Manager listo para operar: {self.initialized}"
        )
        return info_str
    
    def set_n_cores(self):
        """
        Obtiene el número de procesos a utilizar según la configuración.
        """
        max_n_cores = cpu_count()
        if getenv('SIMILARWEB_N_CORES', self.DEFAULT_N_CORES) < 0:
            return max_n_cores
        else:
            if getenv('SIMILARWEB_N_CORES', self.DEFAULT_N_CORES) > max_n_cores:
                return max_n_cores
            else:
                return getenv('SIMILARWEB_N_CORES', self.DEFAULT_N_CORES)

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
        
    def initialize_driver(self):
        """
        Inicializa el driver.
        """
        try:
            # Crear una instancia del driver
            return Driver()
        except Exception as e:
            # Manejar el error al abrir la base de datos
            logger.error(f'Error al inicializar el driver. Error: {e}.')
            return None
        
    ############################################################################
    # Metodos de de uso
    ############################################################################
    def fetch_data(self):
        """
        """
        # Verifico que el driver esta listo para operar
        if self.driver is None:
            logger.error(f'Error al obtener datos. El driver no esta inicializado.')
            return
        
        # Armo la lista de URLs para las tablas
        table_urls = [
            SIMILARWEB_BASE_URL + 'top-websites/',
            SIMILARWEB_BASE_URL + 'top-websites/arts-and-entertainment/tv-movies-and-streaming/',
        ]
        
        # Apartir de esa lista, armos los nombres de los archivos
        table_filenames = [self.generate_filename(x) for x in table_urls]
        
        # Hago el fetch de los HTML
        if not self.skip_scrap:
            self.driver.open_multiple_urls(
                    urls = table_urls,
                    wait_time = self.delay,
                    element_selector = '.app-section__content'
                )
        
        # Para cada top, obtengo la lista de dominios
        html_url_tuple = []
        for table_filename in table_filenames:
            # Obtengo la lista de paginas mas vistas
            table = SimilarWebTopWebsitesTable(filename = table_filename)
            table.fetch_rows()
            html_url_tuple.extend( table.get_url_list() )
        
        # Me quedo solo con las URLs
        html_urls = [x[0] for x in html_url_tuple]
        
        # Mensaje de debug
        if self.DEBUG:
            logger.info(f'Dominions obtenidos desde los contenidos HTML: {html_urls}')
            
        # Verifico que la base de datos esta lista para operar
        if self.database is None:
            logger.error(f'Error al obtener datos. El base de datos no esta incializada.')
            db_urls = []
        else:
            # Consulta SQL
            db_domains = self.database.get_similar_domains()
            db_urls = [get_similarweb_url_tuple(x)[0] for x in db_domains]
        
        # Mensaje de debug
        if self.DEBUG:
            logger.info(f'Dominions obtenidos desde la base de datos: {db_urls}')
            
        # Armos las URLs para las paginas que el usuario ingesa
        user_urls = [get_similarweb_url_tuple(x)[0] for x in self.domains]
        
        # Mensaje de debug
        if self.DEBUG:
            logger.info(f'Dominions pedidos por el usuario: {user_urls}')
            
        # Armo una lista unica
        url_list = list( set( html_urls + db_urls + user_urls ) )
        
        # Limita la lista de IDs de videos al número máximo especificado
        if len(url_list) > self.n_webs_fetch:
            url_list = url_list[:self.n_webs_fetch]
            logger.info(f'CUIDADO: Se recortaron algunos sitios web para scrapear.')
        
        # Muestro la lista final de paginas a obtener
        logger.info('Se va a obtener la informacion de [{}] paginas web'.format(len(url_list)))
        logger.info(f'Lista final de URLs: {url_list}')

        # Obtengo el codigo HTML para esas paginas
        if not self.skip_scrap:
            self.driver.open_multiple_urls(
                    urls = url_list,
                    wait_time = self.delay,
                    element_selector='.app-section__content'
                )
        
        # Apartir de esa lista, armos los nombres de los archivos
        domain_filenames = [self.generate_filename(x) for x in url_list]

        # Recorro la lista de URLs
        for filename in domain_filenames:
            # Obtengo la informacion a partir del contenido HTML
            web_info = SimilarWebWebsite(filename=filename)
            web_info.fetch_data()
            
            if web_info.fetch_status:
                # Obtengo el ID del canal
                try:
                    # Busco el dominio en la base de datos
                    web_info.domain_id = self.get_domain_id( web_info.domain )
                except:
                    logger.warning(f'No se pudo obtener un ID de dominio para el sitio [{web_info.domain}].')

                # Si tengo un dominio valido, lo cargo en la base de datos
                if web_info.domain_id:
                    self.database.insert_similarweb_record( web_info.to_dict() )

                # Mostrar datos de la pagina que fueron guardados en la base de datos
                logger.info(str(web_info))
                
            else:
                logger.error(f'Se produjo un error al intentar obtener los datos para un sitio desde el archivo [{filename}].')

    def get_domain_id(self, domain='youtube.com'):
        """
        Obtiene el ID de dominio para un dominio dado. Si el dominio no existe en la base de datos,
        genera un nuevo ID de dominio.

        Parámetros:
        domain (str): El dominio para el cual se quiere obtener o generar el ID.

        Retorna:
        int: El ID del dominio.
        """
            
        # Verifico que la base de datos esta lista para operar
        if self.database is None:
            logger.error(f'Error al obtener un ID para el dominion [{domain}] datos. El base de datos no esta incializada.')
            
        # Defino la consulta para obtener el ID de dominio
        query = f"SELECT DOMAIN_ID FROM SIMILARWEB_DOMAINS WHERE DOMAIN = '{domain}'"

        # Obtengo el resultado de la consulta
        query_res = self.database.select(query)

        # Si obtengo un resultado, retorno el ID de dominio
        if len(query_res) > 0:
            # El resultado es una lista de tuplas, obtengo el primer elemento
            result = [x[0] for x in query_res]
            domain_id = int(list(set(result))[0])
        else:
            # Si no se encuentra el ID, genero uno nuevo
            query = "SELECT MAX(DOMAIN_ID) FROM SIMILARWEB_DOMAINS"
            result = [x[0] for x in self.database.select(query)]
            max_id = list(set(result))[0]
            domain_id = int(max_id) + 1

        return domain_id

    ############################################################################
    # Utilidades
    ############################################################################
    def generate_filename(self, url):
        """
        Genera un alias para el nombre de archivo basado en la URL.

        Args:
            url (str): URL para la cual se generará el alias.

        Returns:
            str: Alias generado para el nombre de archivo.
        """
        # Remueve protocolo y formatea la URL
        url = url.replace("://", "_")
        url = url.replace("/", "_")
        url = url.replace("#", "_")
        url = url.replace("-", "_")
        cleaned_url = url.replace(".", "_")

        # Elimina los duplicados de guiones bajos
        cleaned_url = '_'.join(cleaned_url.split('_')).strip('_')
        
        # Creo el nombre del archivo
        filename = f'html_{cleaned_url}.dat'
        filepath = os.path.join(self.results_path, filename)

        return filepath

    ############################################################################
    # Gestion de paginas
    ############################################################################
    def get_web(self, domain, delay=15):
        """
        Obtengo los datos de un sitio web en particular
        
        NOTA: Deberia reflejar lo mismo que hace fetch_data pero sin agregar
                nada a la base de datos
        """
        # Verifico que el driver esta listo para operar
        if self.driver is None:
            logger.error(f'Error al obtener datos. El driver no esta inicializado.')
            return
        
        # Me aseguro de tener una espera
        delay = delay or self.delay
        
        # Armo la URL
        url = get_similarweb_url_tuple(domain)[0]
        
        # Obtengo los datos del sitio
        self.driver.open_multiple_urls(
                urls = url,
                wait_time = delay,
                element_selector = '.app-section__content'
            )

        # Armo el nombre del archivo a leer
        filename = self.generate_filename(url)

        # Obtengo la informacion a partir del contenido HTML
        web_info = SimilarWebWebsite(filename=filename)
        web_info.fetch_data()
            
        if web_info.fetch_status:
            # Obtengo el ID del canal
            try:
                # Busco el dominio en la base de datos
                web_info.domain_id = self.get_domain_id( web_info.domain )
            except:
                logger.warning(f'No se pudo obtener un ID de dominio para el sitio [{web_info.domain}].')
            
            # Mostrar datos de la pagina que fueron guardados en la base de datos
            logger.info(str(web_info))
            
        else:
            logger.error(f'Se produjo un error al intentar obtener los datos para un sitio desde el archivo [{filename}].')

    def add_web(self, domain='youtube.com'):
        """
        """
        import datetime

        # Defino la consulta para obtener el ID de dominio
        query = f"SELECT DOMAIN_ID FROM SIMILARWEB_DOMAINS WHERE DOMAIN = '{domain}'"

        # Obtengo el resultado de la consulta
        query_res = self.database.select(query)

        # Si obtengo un resultado, retorno el ID de dominio
        if len(query_res) > 0:
            result = [x[0] for x in query_res]
            domain_id = int(list(set(result))[0])
            logger.info(f'El dominio [{domain}] ya se encuentra en la base de datos con ID [{domain_id}]')
            return
        
        # Genero el dominio para la base de datos
        domain_id = self.get_domain_id(domain)
        
        # Defino la consulta para agregar un dato
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        query = f"INSERT INTO SIMILARWEB_DOMAINS (DOMAIN_ID, DOMAIN, UPDATE_DATE) VALUES (?,?,?)"
        params = (domain_id, domain, current_time)
        
        # Agrego la pagina
        self.database.exec(query,params)
        
        logger.info(f'Se agrego el dominio [{domain}] con ID [{domain_id}] a la base datos')

    def del_web(self, domain=None, domain_id=None):
        # Me fijo si tengo que buscar el dominio
        if domain is not None:
            domain_id = self.get_domain_id(domain=domain)

        # Armo las consultas SQL
        query_1 = f"SELECT * FROM SIMILAWEB_DOMAINS WHERE DOMAIN_ID = {domain_id}"
        query_2 = f"SELECT * FROM SIMILAWEB_RECORDS WHERE DOMAIN_ID = {domain_id}"

        # Busco los datos
        results_1 = self.database.select(query_1)
        results_2 = self.database.select(query_2)
        
        # FIXME: Tengo que terminar aca

        # Muestro los resultados en la tabla SIMILARWEB_DOMAINS
        print('- COINCIDENCIAS EN SIMILARWEB_DOMAINS:')
        if (results_1 is not None):
            if (len(results_1) > 0):
                for res in results_1:
                    print(F'\t{res}')
            else:
                print('\t NO RESULTS')
        else:
            print('\t NO RESULTS')

        # Separacion para que se vea todo mas claro
        print()

        # Muestro los resultados en la tabla SIMILARWEB_RECORDS
        print('- COINCIDENCIAS EN SIMILARWEB_RECORDS:')
        if (results_2 is not None):
            if len(results_2) > 0:
                for res in results_2:
                    print(F'\t{res}')
            else:
                print('\t NO RESULTS')
        else:
            print('\t NO RESULTS')

        if (results_1 is None):
            return
        if (results_2 is None):
            return

        # Checkeo si tengo resultados para borrar y pido confirmacion de borrado
        if ((len(results_1) > 0) or
            (len(results_2) > 0)
        ):
            # Le pregunto al usuario si realmente va a borrar los registros
            ans = None
            while ans not in ['y','n']:
                ans = input('Confirm deleting above records? (y/n): ')

            # Borro definitivamente los registros
            if ans == 'y':
                query_1 = query_1.replace('select *','delete')
                query_2 = query_2.replace('select *','delete')
                # Abro la conexion con la base de datos
                with Database() as db:
                    results_1 = db.select(query_1)
                    results_2 = db.select(query_2)
            else:
                # No hago nada y salgo del programa
                return

if __name__ == '__main__':
    # Creo el objeto
    similarweb_manager = SimilarWebManager()
    
    # Prueba general
    #similarweb_manager.fetch_data()
    
    # Prueba para obtener una pagina
    # similarweb_manager.get_web('youtube.com')
    
    # Prueba para agregar una pagina
    similarweb_manager.add_web('gdsgsdgsgds.com')