# Imports estándar de Python
import os
# import sys

# Añade el directorio raíz del proyecto a sys.path
# current_path = os.path.dirname(os.path.abspath(__file__))
# project_root = os.path.abspath(os.path.join(current_path, '..', '..'))  # Ajusta según la estructura de tu proyecto
# sys.path.append(project_root)

# Imports de terceros
from functools import partial
from multiprocessing import Pool, cpu_count

# Imports locales
from src.youtube.youtube_channel import YoutubeChannel
from src.youtube.youtube_video import YoutubeVideo
from src.youtube.youtube_short import YoutubeShort
from src.youtube.youtube_playlist import YoutubePlaylist
from src.youtube.youtube_api import YoutubeAPI
from src.logger.logger import Logger
from src.database.db import Database
from src.utils.utils import is_url_arg, getenv

################################################################################
# Genero una instancia del Logger
################################################################################
logger = Logger(os.path.basename(__file__)).get_logger()

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
# Define tu función de inicialización de canal independiente
################################################################################
def initialize_youtube_playlist(input_data, verbose=False):
    """
    Inicializa un canal de YouTube utilizando su ID.

    Args:
        input_data (str): El ID o URL del canal de YouTube.

    Returns:
        YoutubeChannel: El objeto de canal de YouTube inicializado.
    """
    try:
        if is_url_arg(input_data):
            playlist = YoutubePlaylist()
            playlist.fetch_html_content(url_type='url', scrap_url=input_data)
            playlist.fetch_data()
        else:
            playlist = YoutubePlaylist(playlist_id=input_data)
            playlist.fetch_data()
        if verbose:
            logger.info(str(playlist))
        return playlist
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
    
################################################################################
# Define tu función de inicialización de short independiente
################################################################################
def initialize_youtube_short(input_data, verbose=False):
    """
    Inicializa un short de YouTube utilizando su ID.

    Args:
        input_data (str): El ID o URL del short de YouTube.

    Returns:
        YoutubeChannel: El objeto de short de YouTube inicializado.
    """
    try:
        if is_url_arg(input_data):
            short = YoutubeShort()
            short.fetch_html_content(url_type='url', scrap_url=input_data)
            short.fetch_data()
        else:
            short = YoutubeShort(short_id=input_data)
            short.fetch_data()
        if verbose:
            logger.info(str(short))
        return short
    except Exception as e:
        logger.error(f'Error al inicializar el short para la ID/URL [{input_data}]. Error: {str(e)}')
        return None

################################################################################
# Define tu función de inicialización de playlist independiente
################################################################################
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
    DEFAULT_N_CHANNELS_FETCH = 10
    DEFAULT_ENABLE_MP = True
    DEFAULT_N_CORES = -1
    DEFAULT_DB_NAME = "latinframe.db"
    DEBUG = False

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
            self.shorts = []
            self.playlists = []
            self.n_channels_fetch = getenv('YOUTUBE_MANAGER_N_CHANNELS_FETCH', self.DEFAULT_N_CHANNELS_FETCH)
            self.enable_mp = getenv('ENABLE_MP', self.DEFAULT_ENABLE_MP)
            self.db_name = getenv('DB_NAME', self.DEFAULT_DB_NAME)
            self.n_cores = self.set_n_cores()
            self.load_channels_from_database = load_channels_from_database
            self.load_videos_from_database = load_videos_from_database
            
            # Inicializar la API de Youtube
            self.youtube_api = self.initialize_youtube_api()

            # Inicializar el objeto Pool para el procesamiento paralelo
            if self.enable_mp:
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
            f"- Nombre de la base de datos: {self.db_name}\n"
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
        if getenv('MP_N_CORES', self.DEFAULT_N_CORES) < 0:
            return max_n_cores
        else:
            if getenv('MP_N_CORES', self.DEFAULT_N_CORES) > max_n_cores:
                return max_n_cores
            else:
                return getenv('MP_N_CORES', self.DEFAULT_N_CORES)

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
            return Database(self.db_name)
        except Exception as e:
            # Manejar el error al abrir la base de datos
            logger.error(f'Error al inicializar la base de datos. Error: {e}.')
            return None

    ############################################################################
    # Gestion de canales de Youtube
    ############################################################################
    def fetch_data(self, initialize_channels=True, initialize_videos=True, initialize_shorts=True, initialize_playlists=True, insert_data_to_db=True):
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
    
            if initialize_shorts:
                self.initialize_shorts()
        
                if self.DEBUG:
                    self.log_shorts_info()
    
            if initialize_playlists:
                self.initialize_playlists()
        
                if self.DEBUG:
                    self.log_playlists_info()
            
            # Esto va a ser lo ultimo que hagamos
            if initialize_videos:
                self.initialize_videos()
                self.log_videos_info()
        
        if insert_data_to_db:
            self.insert_data_to_db()
        
    def initialize_channels(self):
        """
        Inicializa los canales de YouTube.

        Utiliza multiprocessing para inicializar los canales en paralelo si ENABLE_MP es True,
        de lo contrario, inicializa los canales de forma serial.
        """
        if self.enable_mp:
            if self.DEBUG:
                logger.info('Inicializando canales de Youtube en paralelo')
            self.parallel_channel_initialize()
        else:
            if self.DEBUG:
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

        Utiliza multiprocessing para inicializar los videos en paralelo si ENABLE_MP es True,
        de lo contrario, inicializa los videos de forma serial.
        """
        for channel in self.channels:
            # Obtengo la lista de IDs para el canal actual
            video_id_list = channel.video_id_list
            
            if self.enable_mp:
                if self.DEBUG:
                    logger.info('Inicializando videos de Youtube en paralelo')
                self.parallel_video_initialize(video_id_list)
            else:
                if self.DEBUG:
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
    # Gestion de shorts de Youtube
    ############################################################################
    def initialize_shorts(self):
        """
        Inicializa los shorts de YouTube.

        Utiliza multiprocessing para inicializar los shorts en paralelo si ENABLE_MP es True,
        de lo contrario, inicializa los shorts de forma serial.
        """
        for channel in self.channels:
            # Obtengo la lista de IDs para el short actual
            short_id_list = channel.short_id_list
            
            if self.enable_mp:
                if self.DEBUG:
                    logger.info('Inicializando shorts de Youtube en paralelo')
                self.parallel_short_initialize(short_id_list)
            else:
                if self.DEBUG:
                    logger.info('Inicializando shorts de Youtube en serie')
                self.serial_short_initialize(short_id_list)
            
            # Cuando termino le asigno los objetos de tipo short
            # al objeto de tipo short
            channel.shorts = self.shorts
            
            # # Agrego los videos de cada playlist a la lista de IDs
            # # FIXME: Hay que implementar esto
            # for short in channel.shorts:
            #     channel.add_short_ids_to_list(new_video_ids=short.video_ids, source='short')

    def parallel_short_initialize(self, short_id_list):
        """
        Inicializa los shorts de YouTube en paralelo utilizando multiprocessing.Pool.
        """
        self.shorts = []
        try:
            init_func = partial(initialize_youtube_short, verbose=False)
            self.shorts = self.pool.map(init_func, short_id_list)
        except Exception as e:
            logger.error(f'Error al inicializar los shorts en paralelo: {str(e)}')
        
    def serial_short_initialize(self, short_id_list):
        """
        Inicializa los shorts de YouTube de forma serial.
        """
        self.shorts = []
        try:
            for short_id in short_id_list:
                short = initialize_youtube_short(short_id, verbose=False)
                self.shorts.append(short)
        except Exception as e:
            logger.error(f'Error al inicializar los shorts en serie: {str(e)}')
            
    def log_shorts_info(self):
        """
        Registra la información de todos los shorts en el logger.
        """
        for channel in self.channels:
            for short in channel.shorts:
                logger.info(str(short))
    
    ############################################################################
    # Gestion de playlists de Youtube
    ############################################################################
    def initialize_playlists(self):
        """
        Inicializa las playlists de YouTube.

        Utiliza multiprocessing para inicializar las playlists en paralelo si ENABLE_MP es True,
        de lo contrario, inicializa las playlists de forma serial.
        """
        for channel in self.channels:
            # Obtengo la lista de IDs para el playlist actual
            playlist_id_list = channel.playlist_id_list
            
            if self.enable_mp:
                if self.DEBUG:
                    logger.info('Inicializando playlists de Youtube en paralelo')
                self.parallel_playlist_initialize(playlist_id_list)
            else:
                if self.DEBUG:
                    logger.info('Inicializando playlists de Youtube en serie')
                self.serial_playlist_initialize(playlist_id_list)
            
            # Cuando termino le asigno los objetos de tipo playlist
            # al objeto de tipo playlist
            channel.playlists = self.playlists
            
            # Agrego los videos de cada playlist a la lista de IDs
            for playlist in channel.playlists:
                channel.add_video_ids_to_list(new_video_ids=playlist.video_ids, source='playlist')

    def parallel_playlist_initialize(self, playlist_id_list):
        """
        Inicializa las playlists de YouTube en paralelo utilizando multiprocessing.Pool.
        """
        self.playlists = []
        try:
            init_func = partial(initialize_youtube_playlist, verbose=False)
            self.playlists = self.pool.map(init_func, playlist_id_list)
        except Exception as e:
            logger.error(f'Error al inicializar las playlists en paralelo: {str(e)}')
        
    def serial_playlist_initialize(self, playlist_id_list):
        """
        Inicializa las playlists de YouTube de forma serial.
        """
        self.playlists = []
        try:
            for playlist_id in playlist_id_list:
                playlist = initialize_youtube_playlist(playlist_id, verbose=False)
                self.playlists.append(playlist)
        except Exception as e:
            logger.error(f'Error al inicializar las playlists en serie: {str(e)}')
            
    def log_playlists_info(self):
        """
        Registra la información de todos los playlists en el logger.
        """
        for channel in self.channels:
            for playlist in channel.playlists:
                logger.info(str(playlist))
                
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
                if self.n_channels_fetch >= 0 and len(self.channel_ids) >= self.n_channels_fetch:
                    if self.DEBUG:
                        logger.info(f'La lista de canales de YoutubeManager ya está llena.')
                    break
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
                
                channel.add_video_ids_to_list(video_id_list, source='database')
                
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
            logger.error(f"Error al insertar datos para los canales de Youtube en la base de datos. Error: {str(e)}")
            
        try:
            # Inserto los datos de los videos que resultaron exitosos
            for channel in self.channels:
                if channel.fetch_status:
                    for video in channel.videos:
                        if video.fetch_status:
                            self.insert_video_data_to_db(video)
        except Exception as e:
            logger.error(f"Error al insertar datos para los videos de Youtube en la base de datos. Error: {str(e)}")
            
        try:
            # Inserto los datos de los shorts que resultaron exitosos
            for channel in self.channels:
                if channel.fetch_status:
                    for short in channel.shorts:
                        if short.fetch_status:
                            self.insert_short_data_to_db(short)
        except Exception as e:
            logger.error(f"Error al insertar datos para los shorts de Youtube en la base de datos. Error: {str(e)}")
            
        try:
            # Inserto los datos de los shorts que resultaron exitosos
            for channel in self.channels:
                if channel.fetch_status:
                    for playlist in channel.playlists:
                        if playlist.fetch_status:
                            self.insert_playlist_data_to_db(playlist)
        except Exception as e:
            logger.error(f"Error al insertar datos para las playlists de Youtube en la base de datos. Error: {str(e)}")
    
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
            if self.DEBUG:
                logger.info(f"Datos del canal '{channel.channel_id}' insertados en la base de datos.")
        except Exception as e:
            logger.error(f"Error al insertar datos del canal '{channel.channel_id}' en la base de datos: {str(e)}")
    
    def insert_video_data_to_db(self, video):
        """
        Inserta los datos de un video de YouTube en la base de datos.

        Args:
            video (YoutubeVideo): El objeto de video de YouTube del cual se insertarán los datos en la base de datos.
        """
        # Obtener el diccionario de los datos del video
        video_data = video.to_dict()

        # Llamar al método insert_video_record() de la base de datos y pasar el diccionario como argumento
        try:
            self.database.insert_video_record(video_data)
            if self.DEBUG:
                logger.info(f"Datos del video '{video.video_id}' insertados en la base de datos.")
        except Exception as e:
            logger.error(f"Error al insertar datos del video '{video.video_id}' en la base de datos: {str(e)}")
    
    def insert_short_data_to_db(self, short):
        """
        Inserta los datos de un short de YouTube en la base de datos.

        Args:
            short (YoutubeShort): El objeto de short de YouTube del cual se insertarán los datos en la base de datos.
        """
        # Obtener el diccionario de los datos del short
        short_data = short.to_dict()

        # Llamar al método insert_short_record() de la base de datos y pasar el diccionario como argumento
        try:
            self.database.insert_short_record(short_data)
            if self.DEBUG:
                logger.info(f"Datos del short '{short.short_id}' insertados en la base de datos.")
        except Exception as e:
            logger.error(f"Error al insertar datos del canal '{short.short_id}' en la base de datos: {str(e)}")
    
    def insert_playlist_data_to_db(self, playlist):
        """
        Inserta los datos de una playlist de YouTube en la base de datos.

        Args:
            playlist (YoutubePlaylist): El objeto de playlist de YouTube del cual se insertarán los datos en la base de datos.
        """
        # Obtener el diccionario de los datos del playlist
        playlist_data = playlist.to_dict()

        # Llamar al método insert_playlist_record() de la base de datos y pasar el diccionario como argumento
        try:
            self.database.insert_playlist_record(playlist_data)
            if self.DEBUG:
                logger.info(f"Datos del playlist '{playlist.playlist_id}' insertados en la base de datos.")
        except Exception as e:
            logger.error(f"Error al insertar datos del canal '{playlist.playlist_id}' en la base de datos: {str(e)}")
    
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