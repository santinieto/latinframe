from src.youtube.youtube_channel import YoutubeChannel
from src.youtube.youtube_video import YoutubeVideo
from src.youtube.youtube_api import YoutubeAPI
from src.utils.logger import Logger
from src.database.db import Database
from src.utils.utils import is_url_arg
from src.utils.utils import getenv
from functools import partial
from multiprocessing import Pool, cpu_count

################################################################################
# Crear un logger
################################################################################
logger = Logger().get_logger()

################################################################################
# Define tu función de inicialización de canal independiente
################################################################################
def initialize_youtube_channel(input_data, verbose=False):
    """
    Inicializa un canal de YouTube utilizando su ID.

    Args:
        input_data (str): El ID o URL del canal de YouTube.

    Returns:
        YoutubeChannel: El objeto de canal de YouTube inicializado.
    """
    try:
        if is_url_arg(input_data):
            channel = YoutubeChannel()
            channel.fetch_html_content(url_type='url', scrap_url=input_data)
            channel.fetch_data()
        else:
            channel = YoutubeChannel(channel_id=input_data)
            channel.fetch_data()
        if verbose:
            logger.info(str(channel))
        return channel
    except Exception as e:
        logger.error(f'Error al inicializar el canal para la ID/URL [{input_data}]. Error: {str(e)}')
        return None
    
################################################################################
# Define tu función de inicialización de video independiente
################################################################################
def initialize_youtube_video(input_data, verbose=False):
    """
    Inicializa un video de YouTube utilizando su ID.

    Args:
        input_data (str): El ID o URL del video de YouTube.

    Returns:
        YoutubeChannel: El objeto de video de YouTube inicializado.
    """
    try:
        if is_url_arg(input_data):
            video = YoutubeVideo()
            video.fetch_html_content(url_type='url', scrap_url=input_data)
            video.fetch_data()
        else:
            video = YoutubeVideo(video_id=input_data)
            video.fetch_data()
        if verbose:
            logger.info(str(video))
        return video
    except Exception as e:
        logger.error(f'Error al inicializar el video para la ID/URL [{input_data}]. Error: {str(e)}')
        return None

def initialize_youtube_video_from_db(video_id, verbose=False):
    """
    Inicializa un video de YouTube utilizando su ID.

    Args:
        video_id (str): El ID del video de YouTube.

    Returns:
        YoutubeChannel: El objeto de video de YouTube inicializado.
    """
    try:
        with Database(YoutubeManager.DB_NAME) as db:
            query_1 = f"SELECT * FROM VIDEO WHERE VIDEO_ID = '{video_id}'"
            query_2 = f"SELECT * FROM VIDEO_RECORDS WHERE VIDEO_ID = '{video_id}' ORDER BY UPDATE_DATE DESC"
            result_1 = db.select(query_1)[0]
            result_2 = db.select(query_2)[0]
            
            info_dict = {
                'video_id': result_1[0],
                'title': result_1[1],
                'channel_id': result_1[2],
                'channel_name': '',
                'views': result_2[2],
                'likes': result_2[4],
                'length': result_1[3],
                'comment_count': result_2[5],
                'mvm': result_2[3],
                'tags': result_1[4],
                'publish_date': result_1[5],
            }
            
            video = YoutubeVideo(info_dict=info_dict)
            print(str(video))
    except Exception as e:
        logger.error(f'Error al inicializar el video {video_id}: {str(e)}')
        return None

################################################################################
# Clase principal
################################################################################
class YoutubeManager:
    ############################################################################
    # Atributos globables
    ############################################################################
    # Atributo de clase para almacenar la instancia única
    _instance = None

    # Configuraciones por defecto
    ENABLE_MP = getenv('ENABLE_MP', True)
    N_CORES = getenv('MP_N_CORES', -1)
    DB_NAME = getenv('DB_NAME', "latinframe.db")
    DEBUG = True

    ############################################################################
    # Metodos de incializacion
    ############################################################################
    # Cuando solicito crear una instancia me aseguro que
    # si ya hay una creada, devuelvo esa misma
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, load_channels_from_database=True, load_videos_from_database=True, channel_ids=[]):
        # Evitar la inicialización múltiple
        # verificando si existe el atributo initialized en la clase
        if not hasattr(self, 'initialized'):
            self.channel_ids = channel_ids
            self.channels = []
            self.videos = []
            self.n_cores = self.set_n_cores()
            self.load_channels_from_database = load_channels_from_database
            self.load_videos_from_database = load_videos_from_database
            
            # Inicializar la API de Youtube
            self.youtube_api = self.initialize_youtube_api()

            # Inicializar el objeto Pool para el procesamiento paralelo
            if self.ENABLE_MP:
                self.pool = Pool(processes=self.n_cores)
            else:
                self.pool = None

            # Inicializar la base de datos
            self.database = self.initialize_database()
            
            # Flag para indicar si la inicialización fue exitosa
            if (self.youtube_api and self.database):
                self.initialized = True
            else:
                self.initialized = False
            
            # Inicializar la base de datos si load_from_database es True
            if self.load_channels_from_database:
                self.load_channel_ids_from_database()
            
            # Muestro los datos si fuera necesario
            if self.DEBUG:
                logger.info(str(self))
    
    def __str__(self):
        """
        Devuelve una representación de cadena con los datos relevantes de la clase YoutubeManager.
        """
        youtube_api_msg = "API de YouTube: No inicializada" if self.youtube_api is None else "API de YouTube: Inicializada"
        database_msg = "Base de datos: No inicializada" if self.database is None else "Base de datos: Inicializada"
        
        info_str = (
            f"- Número de canales a analizar: {len(self.channel_ids)}\n"
            f"- IDs de los canales a analizar: {self.channel_ids}\n"
            f"- Número de núcleos a utilizar (solo si se usa multithreading): {self.n_cores}\n"
            f"- Nombre de la base de datos: {self.DB_NAME}\n"
            f"- {youtube_api_msg}\n"
            f"- {database_msg}\n"
            f"- Youtube Manager listo para operar: {self.initialized}"
        )
        return info_str
    
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

    def initialize_youtube_api(self):
        """
        Crea una instancia de la API de Youtube.
        """
        try:
            return YoutubeAPI()
        except Exception as e:
            logger.error(f'Error al inicializar la API de Youtube. Error: {e}.')
            return None

    def initialize_database(self):
        """
        Inicializa la base de datos.
        """
        try:
            # Crear una instancia de Database y abrir la base de datos
            return Database(self.DB_NAME)
        except Exception as e:
            # Manejar el error al abrir la base de datos
            logger.error(f'Error al inicializar la base de datos. Error: {e}.')
            return None

    ############################################################################
    # Gestion de canales de Youtube
    ############################################################################
    def fetch_data(self, initialize_channels=True, initialize_videos=True, insert_data_to_db=True):
        """
        Ejecuta el proceso de scrap según las opciones proporcionadas.
        """
        if initialize_channels:
            self.initialize_channels()
        
            if self.DEBUG:
                self.log_channels_info()
            
            # Inicializar la base de datos si load_from_database es True
            if self.load_videos_from_database:
                self.load_video_ids_from_database()
    
            if initialize_videos:
                self.initialize_videos()
        
                if self.DEBUG:
                    self.log_videos_info()
        
        if insert_data_to_db:
            self.insert_data_to_db()
        
    def initialize_channels(self):
        """
        Inicializa los canales de YouTube.

        Utiliza multiprocessing para inicializar los canales en paralelo si ENABLE_MP es True,
        de lo contrario, inicializa los canales de forma serial.
        """
        if self.ENABLE_MP:
            logger.info('Inicializando canales de Youtube en paralelo')
            self.parallel_channel_initialize()
        else:
            logger.info('Inicializando canales de Youtube en serie')
            self.serial_channel_initialize()

    def parallel_channel_initialize(self):
        """
        Inicializa los canales de YouTube en paralelo utilizando multiprocessing.Pool.
        """
        try:
            # Utiliza functools.partial para pasar los argumentos fijos a initialize_youtube_channel
            init_func = partial(initialize_youtube_channel)
            # Ejecuta initialize_youtube_channel para cada ID de canal en paralelo
            self.channels = self.pool.map(init_func, self.channel_ids)
        except Exception as e:
            logger.error(f'Error al inicializar los canales en paralelo: {str(e)}')
            
    def serial_channel_initialize(self):
        """
        Inicializa los canales de YouTube de forma serial.
        """
        self.channels = []
        try:
            for channel_id in self.channel_ids:
                channel = initialize_youtube_channel(channel_id)
                self.channels.append(channel)
        except Exception as e:
            logger.error(f'Error al inicializar los canales en serie: {str(e)}')
            
    def log_channels_info(self):
        """
        Registra la información de todos los canales en el logger.
        """
        for channel in self.channels:
            logger.info(str(channel))

    ############################################################################
    # Gestion de videos de Youtube
    ############################################################################
    def initialize_videos(self):
        """
        Inicializa los videos de YouTube.

        Utiliza multiprocessing para inicializar los canales en paralelo si ENABLE_MP es True,
        de lo contrario, inicializa los canales de forma serial.
        """
        for channel in self.channels:
            # Obtengo la lista de IDs para el canal actual
            video_id_list = channel.video_id_list
            
            if self.ENABLE_MP:
                logger.info('Inicializando videos de Youtube en paralelo')
                self.parallel_video_initialize(video_id_list)
            else:
                logger.info('Inicializando videos de Youtube en serie')
                self.serial_video_initialize(video_id_list)
            
            # Cuando termino le asigno los objetos de tipo video
            # al objeto de tipo canal
            channel.videos = self.videos

    def parallel_video_initialize(self, video_id_list):
        """
        Inicializa los canales de YouTube en paralelo utilizando multiprocessing.Pool.
        """
        self.videos = []
        try:
            init_func = partial(initialize_youtube_video, verbose=False)
            self.videos = self.pool.map(init_func, video_id_list)
        except Exception as e:
            logger.error(f'Error al inicializar los videos en paralelo: {str(e)}')
        
    def serial_video_initialize(self, video_id_list):
        """
        Inicializa los canales de YouTube de forma serial.
        """
        self.videos = []
        try:
            for video_id in video_id_list:
                video = initialize_youtube_video(video_id, verbose=False)
                self.videos.append(video)
        except Exception as e:
            logger.error(f'Error al inicializar los videos en serie: {str(e)}')
            
    def log_videos_info(self):
        """
        Registra la información de todos los canales en el logger.
        """
        for channel in self.channels:
            for video in channel.videos:
                logger.info(str(video))
                
    ############################################################################
    # Interacciones con la base de datos
    ############################################################################
    def load_channel_ids_from_database(self):
        """
        Carga los canales de YouTube desde la base de datos y los agrega a la
        lista channel_ids.
        """
        if not self.database:
            logger.error("La base de datos no está inicializada.")
            return

        try:
            # Obtener los IDs de los canales de la base de datos
            channel_ids_from_db = self.database.get_youtube_channel_data(target='CHANNEL_ID', sort='asc')

            # Agregar los canales a la lista channels si no están ya presentes
            for channel_id in channel_ids_from_db:
                if channel_id not in self.channel_ids:
                    self.channel_ids.append(channel_id)
                else:
                    if self.DEBUG:
                        logger.info(f'El canal [{channel_id}] ya se encuentra en la lista.')
        except Exception as e:
            logger.error(f"Error al cargar los canales desde la base de datos. Error: {e}.")
            
    def load_video_ids_from_database(self):
        """
        Carga los videos de YouTube para cada canal desde la base de datos y
        los agrega a la lista de video_ids de cada canal.
        """
        if not self.database:
            logger.error("La base de datos no está inicializada.")
            return

        try:
            # Para cada canal obtengo los videos
            for channel in self.channels:
                if self.DEBUG:
                    logger.info(f'Cargando videos de YouTube desde la base de datos para el canal [{channel.channel_id}].')
                    
                video_id_list = self.database.get_youtube_video_ids(channel_id_list=channel.channel_id)
                if self.DEBUG:
                    logger.info(f'Lista de videos a cargar: {video_id_list}')
                
                channel.add_video_ids_to_list(video_id_list)
                
        except Exception as e:
            logger.error(f"Error al cargar los canales desde la base de datos. Error: {e}.")
    
    def insert_data_to_db(self):
        """
        Inserta los datos obtenidos de YouTube en la base de datos.
        """
        try:
            # Inserto los datos de los canales que resultaron exitosos
            for channel in self.channels:
                if channel.fetch_status:
                    self.insert_channel_data_to_db(channel)
        except Exception as e:
            logger.error(f"Error al insertar datos para los canales de Youtube en la base de datos: {str(e)}")
            
        try:
            # Inserto los datos de los canales que resultaron exitosos
            for channel in self.channels:
                if channel.fetch_status:
                    for video in channel.videos:
                        if video.fetch_status:
                            self.insert_video_data_to_db(video)
        except Exception as e:
            logger.error(f"Error al insertar datos para los videos de Youtube en la base de datos: {str(e)}")
    
    def insert_channel_data_to_db(self, channel):
        """
        Inserta los datos de un canal de YouTube en la base de datos.

        Args:
            channel (YoutubeChannel): El objeto de canal de YouTube del cual se insertarán los datos en la base de datos.
        """
        # Obtener el diccionario de los datos del canal
        channel_data = channel.to_dict()

        # Llamar al método insert_channel_record() de la base de datos y pasar el diccionario como argumento
        try:
            self.database.insert_channel_record(channel_data)
            logger.info(f"Datos del canal '{channel.channel_id}' insertados en la base de datos.")
        except Exception as e:
            logger.error(f"Error al insertar datos del canal '{channel.channel_id}' en la base de datos: {str(e)}")
    
    def insert_video_data_to_db(self, video):
        """
        Inserta los datos de un video de YouTube en la base de datos.

        Args:
            channel (YoutubeVideo): El objeto de video de YouTube del cual se insertarán los datos en la base de datos.
        """
        # Obtener el diccionario de los datos del video
        video_data = video.to_dict()

        # Llamar al método insert_channel_record() de la base de datos y pasar el diccionario como argumento
        try:
            self.database.insert_video_record(video_data)
            logger.info(f"Datos del canal '{video.channel_id}' insertados en la base de datos.")
        except Exception as e:
            logger.error(f"Error al insertar datos del canal '{video.channel_id}' en la base de datos: {str(e)}")
    
if __name__ == "__main__":
    import argparse
    
    # Configuración del parser de argumentos
    parser = argparse.ArgumentParser(description='Gestor de YouTube', add_help=False)

    # Argumentos comunes
    parser.add_argument('--help', action='store_true', help='Mostrar mensaje de ayuda')
    parser.add_argument('--all', action='store_true', help='Ejecutar todos los scraps')
    parser.add_argument('--channels', type=str, nargs='+', default=[], help='Canales adicionales a buscar')
    parser.add_argument('--video', type=str, help='ID o URL del video')
    parser.add_argument('--channel', type=str, help='ID o URL del canal')
    parser.add_argument('--add', action='store_true', help='Agregar a la base de datos')
    parser.add_argument('--delete', type=str, help='Eliminar de la base de datos')
    parser.add_argument('--save_html', action='store_true', help='Guardar contenido HTML')

    # Análisis de los argumentos de la línea de comandos
    args = parser.parse_args()

    # Llamada a la función correspondiente según el comando
    # handle_youtube_args(args)