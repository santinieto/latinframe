# Librerias que voy a necesitar
from googleapiclient.discovery import build
from googleapiclient.errors    import HttpError
import json
from datetime import datetime
import pandas   as pd

# Importo mis modulos y funciones
from src.utils.environment import set_environment
from src.utils.utils import transform_duration_format
from src.utils.utils import safe_get_from_json
from src.utils.utils import cprint
from src.utils.utils import getenv
from src.logger.logger import Logger
import os

# Crear un logger
logger = Logger(os.path.basename(__file__)).get_logger()

# Creo la clase para levantar la API
class YoutubeAPI:
    ############################################################################
    # Atributos globables
    ############################################################################
    # Atributo de clase para almacenar la instancia única
    _instance = None

    # Configuraciones por defecto
    DEFAULT_API_KEY = 'YOUR_DEFAULT_API_KEY'
    DEFAULT_N_VIDEOS_FETCH = 10
    DEFAULT_PAGE_RESULTS = 50
    DEBUG = False

    # Lista de códigos de error considerados críticos
    CRITICAL_ERRORS = [400, 403, 500]

    ############################################################################
    # Metodos de incializacion
    ############################################################################
    # Cuando solicito crear una instancia me aseguro que
    # si ya hay una creada, devuelvo esa misma
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def reset(cls):
        logger.info(f'Reset de la API de Youtube.')
        if cls._instance is not None:
            cls._instance = None
            cls._instance.__init__()

    def __init__(self, api_key=None):
        # Evitar la inicialización múltiple
        # verificando si existe el atributo initialized en la clase
        if not hasattr(self, 'initialized'):
            
            # Obtengo la key de la API, si no la encuentro, cargo una por
            # defecto.
            self.api_key = getenv('YOUTUBE_API_KEY', self.DEFAULT_API_KEY)
            
            # Inicializa el cliente de la API de YouTube.
            self.enabled = self.initialize_youtube_client()
            
            # Variables por defecto
            self.request = None
            self.n_videos_fetch = getenv('YOUTUBE_API_N_VIDEOS_FETCH', self.DEFAULT_N_VIDEOS_FETCH)
            self.page_results = getenv('YOUTUBE_API_PAGE_RESULTS', self.DEFAULT_PAGE_RESULTS)
            self.last_request_success = True
        
            # Comprobaciones de seguridad
            self.n_videos_fetch = max(self.n_videos_fetch, 0) # Me aseguro que no sea menor que 0
            self.page_results = max(self.page_results, 1) # Me aseguro que no sea menor que 1
            
            # Marca la instancia como inicializada
            self.initialized = True
            
            # Ejecuto el test de sanidad
            self.health_check()
            # Si la peticion de sanidad fallo, entonces deshabilito la API
            if self.last_request_success is False:
                self.disable_api()
            
            if self.DEBUG:
                logger.info(f'Se ha creado la clase para la API de YouTube. Estado final: {self.enabled}')
            
        if self.DEBUG:
            logger.info(f'Parametros de la clase de la API de YouTube:')
            logger.info(f'\t- Clave unica cargada: {self.api_key}')
            logger.info(f'\t- API en funcionamiento: {self.enabled}')
            logger.info(f'\t- Cantidad de videos a actualizar por canal: {self.n_videos_fetch}')

    def initialize_youtube_client(self):
        """Inicializa el cliente de la API de YouTube."""
            
        if self.DEBUG:
            logger.debug(f'Inicializando comunicacion con la API de YouTube...')
                
        try:
            self.youtube = build('youtube', 'v3', developerKey=self.api_key)
            return True
        except Exception as e:
            self.youtube = None
            cprint(f'Error al iniciar la conexión con la API de YouTube: {e}')
            return False

    def get_n_videos_fetch(self):
        """Obtiene el número de videos a buscar desde las variables de entorno."""
            
        if self.DEBUG:
            logger.debug(f'Obteniendo el valor por defecto de videos a actualizar por canal...')
            
        try:
            n_videos_fetch = int(os.getenv('youtube_nvideos_fecth', self.DEFAULT_N_VIDEOS_FETCH))
            return max(n_videos_fetch, 0)  # Garantiza que no sea negativo
        except ValueError as e:
            logger.warning(f'Valor inválido para youtube_nvideos_fecth, usando valor por defecto: {self.DEFAULT_N_VIDEOS_FETCH}')
            return self.DEFAULT_N_VIDEOS_FETCH
        
    def is_enabled(self):
        """Verifica si la instancia está en funcionamiento."""
        return self.enabled

    def enable_api(self):
        """Habilita la API de YouTube."""
        self.enabled = True
        os.environ["youtube_api_en"] = 'True'
        logger.info('La API de YouTube ha sido habilitada.')

    def disable_api(self):
        """Deshabilita la API de YouTube."""
        self.enabled = False
        os.environ["youtube_api_en"] = 'False'
        logger.warning('La API de YouTube ha sido deshabilitada debido a un error crítico.')

    def execute(self):
        """Ejecuta la solicitud actual a la API de YouTube."""
        
        if not self.is_enabled():
            self.last_request_success = False
            return {'message': 'La API está deshabilitada'}
        
        # Se intenta ejecutar la solicitud almacenada en self.request
        # dentro de un bloque try
        try:
            response = self.request.execute()
            # Si la solicitud se ejecuta con éxito, se devuelve la respuesta.
            self.last_request_success = True
            return response
        
        # Si se produce un error (HttpError), se captura y se maneja dentro
        # del bloque except.
        except HttpError as e:
            # Se analiza el mensaje de error para determinar si se ha superado
            # la cuota diaria de la API de YouTube.
            error_content = json.loads(e.content)
            error_message = error_content['error']['errors'][0]['reason']
            error_code = error_content['error']['code']
            
            # Si se superó la cuota, se deshabilita la API y se devuelve un
            # diccionario indicando el código de error, el mensaje de error
            # y que la cuota fue excedida.
            if 'quota' in error_message.lower():
                logger.warning('Se alcanzó la cuota máxima en la API de YouTube, será deshabilitada')
                self.disable_api()
                # Si se produjo un error, dejamos registro
                self.last_request_success = False
                return {'error_code': error_code, 'error_message': error_message, 'quota_exceeded': True}

            if error_code in self.CRITICAL_ERRORS:
                logger.warning('Se produjo un error CRITICO al procesar la solicitud.')
                self.disable_api()
            
            # Si el error no se debió a la cuota, se registra un mensaje de
            # error y se devuelve un diccionario indicando el código de error,
            # el mensaje de error y que la cuota no fue excedida.
            logger.error(f'Error al procesar la solicitud a la API de YouTube: {error_message}')
            # Si se produjo un error, dejamos registro
            self.last_request_success = False
            return {'error_code': error_code, 'error_message': error_message, 'quota_exceeded': False}
        
        # Manejar un error desconocido
        except Exception as e:
            # Manejar otros errores de manera específica, si es posible
            logger.error(f'Error desconocido al ejecutar la solicitud a la API de YouTube. Error: {e}')
            self.last_request_success = False
            return {'message': 'Error desconocido al ejecutar la solicitud a la API de YouTube'}
        
    def health_check(self):
        "Intento obtener los datos del canal de Google Developers"
        try:
            self.request = self.youtube.channels().list(
                part='snippet',
                id='UC_x5XG1OV2P6uZZ5FSM9Ttw'
            )
            self.execute()
        except Exception as e:
            logger.error(f'Error en health_check: {e}')

    ############################################################################
    # Metodos de aplicacion
    ############################################################################
    def fetch_channel_data(self, channel_id=None):
        """
        Obtiene los datos relevantes de un canal de YouTube dado su ID.

        Args:
            channel_id (str): El ID del canal de YouTube.

        Returns:
            dict or None: Un diccionario con los datos del canal si la operación tiene éxito, o None si ocurre un error.
                El diccionario contiene:
                - 'channel_id': ID del canal.
                - 'channel_name': Nombre del canal.
                - 'custom_url': URL personalizada del canal.
                - 'publish_date': Fecha de publicación del canal.
                - 'country': País del canal.
                - 'main_playlist': ID de la lista de reproducción principal del canal.
                - 'channel_views': Vistas totales del canal.
                - 'n_videos': Número total de videos en el canal.
                - 'subscribers': Número de suscriptores del canal.
                - 'daily_subs': Suscriptores diarios (actualmente 0).
                - 'monthly_subs': Suscriptores mensuales (actualmente 0).
                - 'video_ids_list': Lista de IDs de videos de la lista de reproducción principal del canal.
                - 'subchannels': Lista de IDs de los canales a los que está suscrito el canal principal.
                - 'playlist_id_list': Lista de IDs de listas de reproducción del canal.
        """
        # Verificar si la API de YouTube está habilitada
        if not self.is_enabled():
            logger.warning('La API de YouTube no está habilitada. Saliendo de la función fetch_channel_data.')
            return None
        
        # Si no se le da un ID de canal salgo de la ejecucion
        if channel_id is None:
            raise ValueError(f'Se necesita un canal para obtener informacion en la funcion fetch_channel_data().')
    
        try:
            # Realiza una solicitud para obtener los datos del canal desde la API de YouTube
            self.request = self.youtube.channels().list(
                part = 'snippet,contentDetails,statistics',
                id = channel_id
            )
            response = self.execute()
            
            # Verifica si se activó el modo de depuración y muestra la respuesta de la API
            if self.DEBUG:
                logger.debug(f'Youtube API response: {str(response)}')
            
            # Extrae los datos relevantes del primer elemento de la respuesta
            item          = response['items'][0]
            channel_name  = safe_get_from_json(item, ['snippet', 'title'], 'Unknown')
            channel_url   = safe_get_from_json(item, ['snippet', 'customUrl'], 'Unknown')
            publish_date  = safe_get_from_json(item, ['snippet', 'publishedAt'], 'Unknown')
            country       = safe_get_from_json(item, ['snippet', 'country'], 'Unknown')
            channel_views = safe_get_from_json(item, ['statistics', 'viewCount'], 0)
            n_videos      = safe_get_from_json(item, ['statistics', 'videoCount'], 0)
            subscribers   = safe_get_from_json(item, ['statistics', 'subscriberCount'], 0)
            main_playlist = safe_get_from_json(item, ['contentDetails', 'relatedPlaylists', 'uploads'], 'Unknown')
            
            # Retorna un diccionario con los datos del canal
            return {
                'channel_id': channel_id,
                'channel_name': channel_name,
                'channel_url': channel_url,
                'publish_date': publish_date,
                'country': country,
                'main_playlist': main_playlist,
                'channel_views': channel_views,
                'n_videos': n_videos,
                'subscribers': subscribers,
                'daily_subs': 0,
                'monthly_subs': 0,
                'video_id_list': self.fetch_playlist_videos(main_playlist, page_results=self.page_results),
                'subchannels': [], # subscriptionForbidden --> self.fetch_channel_subchannels(channel_id),
                'playlist_id_list': self.fetch_channel_playlists(channel_id),
            }
        
        # Captura errores específicos y registra mensajes de error con información detallada
        except KeyError as e:
            logger.error(f'Error de tipo KeyError al obtener los datos para el canal {channel_id}: {e}')
            return None
        except IndexError as e:
            logger.error(f'Error de tipo IndexError al obtener los datos para el canal {channel_id}: {e}')
            return None
        except Exception as e:
            logger.error(f'Error de tipo Exception al obtener los datos para el canal {channel_id}: {e}')
            return None
        
    def fetch_channel_subchannels(self, channel_id, page_results=None):
        """
        Recupera los subcanales de un canal dado.

        Args:
            channel_id (str): ID del canal del que se van a recuperar los subcanales.
            page_results (int, optional): Número máximo de resultados por página. Si no se proporciona,
                                        se utiliza el valor predeterminado de la clase.

        Returns:
            list: Una lista de ID de video de los subcanales del canal especificado.

        """
        # Verificar si la API está habilitada
        if not self.is_enabled():
            logger.warning('La API de YouTube no está habilitada. Saliendo de la función fetch_channel_subchannels().')
            return []
        
        # Si no se proporciona page_results, se utiliza el valor predeterminado de la clase
        if page_results is not None and page_results <= 0:
            raise ValueError(f'El número de resultados por página debe ser mayor que cero: {page_results}')
            
        # Se hace la solicitud a la API de YouTube para obtener los subcanales del canal
        self.request = self.youtube.subscriptions().list(
            part='snippet',
            channelId=channel_id,
            maxResults=page_results
        )
        response = self.execute()
        
        try:
            # Se recuperan los ID de video de los subcanales de la respuesta
            return [elemento['id']['videoId'] for elemento in response.get('items', [])]
        except Exception as e:
            # En caso de error, se registra y se devuelve una lista vacía
            logger.error(f'Error al obtener los subcanales del canal {channel_id}: {e}')
            return []

    def fetch_channel_playlists(self, channel_id, page_results=None):
        """
        Recupera las listas de reproducción de un canal dado.

        Args:
            channel_id (str): ID del canal del que se van a recuperar las listas de reproducción.
            page_results (int, optional): Número máximo de resultados por página. Si no se proporciona,
                                        se utiliza el valor predeterminado de la clase.

        Returns:
            list: Una lista de ID de las listas de reproducción del canal especificado.

        """
        # Verificar si la API está habilitada
        if not self.is_enabled():
            logger.warning('La API de YouTube no está habilitada. Saliendo de la función fetch_channel_playlists().')
            return []
        
        # Si no se proporciona page_results, se utiliza el valor predeterminado de la clase
        if page_results is not None and page_results <= 0:
            raise ValueError(f'El número de resultados por página debe ser mayor que cero: {page_results}')
            
        # Se hace la solicitud a la API de YouTube para obtener las listas de reproducción del canal
        self.request = self.youtube.playlists().list(
            part='snippet',
            channelId=channel_id,
            maxResults=page_results
        )
        response = self.execute()
        
        try:
            # Se recuperan los ID de las listas de reproducción de la respuesta
            return [elemento['id'] for elemento in response.get('items', [])]
        except Exception as e:
            # En caso de error, se registra y se devuelve una lista vacía
            logger.error(f'Error al obtener las listas de reproducción del canal {channel_id}: {e}')
            return []
        
    def fetch_playlist_videos(self, playlist_id='UUz1f7i31i-zh4kwOA0Y-bTA', n_videos_fetch=None, page_results=None):
        """
        Recupera todos los videos de una lista de reproducción especificada.

        Args:
            playlist_id (str, optional): ID de la lista de reproducción. Por defecto, se utiliza una lista de reproducción predeterminada.
            n_videos_fetch (int, optional): Número total de videos que se desean recuperar. Si no se proporciona, se utiliza el valor predeterminado de la clase.
            page_results (int, optional): Número máximo de resultados por página. Si no se proporciona, se utiliza el valor predeterminado de la clase.

        Returns:
            list: Una lista de IDs de video de la lista de reproducción especificada.

        Raises:
            ValueError: Si el número de videos a recuperar o el número de resultados por página es menor o igual a cero.

        """
        # Verificar si la API está habilitada
        if not self.is_enabled():
            logger.warning('La API de YouTube no está habilitada. Saliendo de la función fetch_playlist_videos().')
            return []
    
        # Verificar si los valores son válidos
        if n_videos_fetch is not None and n_videos_fetch <= 0:
            raise ValueError(f'El número de videos a recuperar debe ser mayor que cero: {n_videos_fetch}')
        if page_results is not None and page_results <= 0:
            raise ValueError(f'El número de resultados por página debe ser mayor que cero: {page_results}')
        
        # Establecer valores predeterminados si no se proporcionan
        n_videos_fetch = n_videos_fetch if n_videos_fetch is not None else self.n_videos_fetch
        page_results = page_results if page_results is not None else self.page_results
        
        # Si la cantidad de resultados por página que se solicita es mayor que la cantidad total de videos que se desean recuperar,
        # ajustar la cantidad de resultados por página al número total de videos que se desean recuperar
        if page_results > n_videos_fetch:
            page_results = n_videos_fetch
        
        # Inicializar las variables
        video_ids = []
        remaining_videos = n_videos_fetch
        next_page_token = None
        
        # Comenzar a obtener videos
        while remaining_videos > 0:
            try:
                # Realizar la solicitud a la API de YouTube para obtener los videos de la lista de reproducción
                self.request = self.youtube.playlistItems().list(
                    part='contentDetails',
                    playlistId=playlist_id,
                    maxResults=page_results,
                    pageToken=next_page_token
                )
                response = self.execute()
                
                # Procesar la respuesta para obtener los IDs de video
                for item in response.get('items', []):
                    video_id = item['contentDetails']['videoId']
                    video_ids.append(video_id)
                    remaining_videos -= 1
                    
                    # Salir del bucle si se han recopilado todos los videos necesarios
                    if remaining_videos <= 0:
                        break
                
                # Verificar si hay más datos que cargar
                next_page_token = response.get('nextPageToken')
                
                # Terminar la ejecución si no hay más videos
                if not next_page_token:
                    break
                
            except Exception as e:
                # Manejar errores y registrarlos
                logger.error(f'Error al obtener los videos de la lista de reproducción {playlist_id}: {e}')
                break
        
        return video_ids
    
    def fetch_video_data(self, video_id):
        """
        Obtiene datos relevantes de un video de YouTube dado su ID.
        
        Args:
            video_id (str): El ID del video de YouTube.
        
        Returns:
            dict: Un diccionario con los datos del video.
                - 'id': ID del video.
                - 'title': Título del video.
                - 'channel_id': ID del canal al que pertenece el video.
                - 'channel_name': Nombre del canal al que pertenece el video.
                - 'publish_date': Fecha de publicación del video (en formato 'YYYY/MM/DD HH:MM:SS').
                - 'tags': Etiquetas del video separadas por '/'.
                - 'views': Número de vistas del video.
                - 'likes': Número de "me gusta" del video.
                - 'comments_cnt': Número de comentarios del video.
                - 'length': Duración del video en formato 'HH:MM:SS'.
                - 'mvm': Tiempo medio de visualización del video (no implementado en la versión actual).
        """
        # Verificar si la API de YouTube está habilitada
        if not self.is_enabled():
            logger.warning('La API de YouTube no está habilitada. Saliendo de la función fetch_video_data.')
            return {}
        
        # Si no se le da un ID de canal salgo de la ejecucion
        if not video_id:
            raise ValueError('Se necesita un ID de video para obtener información en la función fetch_video_data().')
        
        # Inicializar el diccionario de datos
        data = {}
        
        try:
            # Realizar una solicitud para obtener los datos del video desde la API de YouTube
            self.request = self.youtube.videos().list(
                part='contentDetails,id,snippet,statistics',
                id=video_id
            )
            response = self.execute()
            
            # Obtener los datos del video si la respuesta es válida
            if 'items' in response and response['items']:
                item = response['items'][0]
                
                # Obtener el ID del video
                data['video_id'] = item.get('id', video_id)
                
                # Obtener el título del video
                data['title'] = item['snippet'].get('title', 'Unknown')
                
                # Obtener el ID y nombre del canal del video
                snippet = item.get('snippet', {})
                data['channel_id'] = snippet.get('channelId', 'Unknown channel ID')
                data['channel_name'] = snippet.get('channelTitle', 'Unknown channel name')
                
                # Obtener la fecha de publicación del video
                published_at = snippet.get('publishedAt')
                if published_at:
                    publish_date = datetime.strptime(published_at, '%Y-%m-%dT%H:%M:%SZ')
                    data['publish_date'] = publish_date.strftime('%Y/%m/%d %H:%M:%S')
                else:
                    data['publish_date'] = '00/00/00'
                
                # Obtener las etiquetas del video
                tags = snippet.get('tags', [])
                data['tags'] = '/'.join(tags)
                
                # Obtener el número de vistas del video
                statistics = item.get('statistics', {})
                data['views'] = statistics.get('viewCount', 0)
                
                # Obtener el número de "me gusta" del video
                data['likes'] = statistics.get('likeCount', 0)
                
                # Obtener el número de comentarios del video
                data['comment_count'] = statistics.get('commentCount', 0)
                
                # Obtener la duración del video
                content_details = item.get('contentDetails', {})
                duration = content_details.get('duration', 'PT0S')
                data['length'] = transform_duration_format(duration)
            
        except Exception as e:
            logger.error(f'Se produjo un error al obtener la información para el video {video_id}. Error: {e}')
        
        # Placeholder para el tiempo medio de visualización del video (actualmente no implementado)
        data['mvm'] = '00:00:00'
        
        return data
    
    def fetch_short_data(self, short_id):
        """
        Obtiene datos relevantes de un short de YouTube dado su ID.
        
        Args:
            short_id (str): El ID del short de YouTube.
        
        Returns:
            Lo mismo que retorna la funcion fetch_video_data()
        """
        data = self.fetch_video_data(short_id)
        data['short_id'] = data['video_id']
        return data
    
    def fetch_playlist_data(self, playlist_id):
        """
        Obtiene datos relevantes de una playlist de YouTube dado su ID.
        
        Args:
            playlist_id (str): El ID de la playlist de YouTube.
        
        Returns:
            dict: Un diccionario con los datos de la playlist.
                - 'id': ID de la playlist.
                - 'title': Título de la playlist.
                - 'channel_id': ID del canal al que pertenece el video.
                - 'channel_name': Nombre del canal al que pertenece el video.
                - 'publish_date': Fecha de publicación de la playlist (en formato 'YYYY/MM/DD HH:MM:SS').
                - 'views': Número de vistas de la playlist.
                - 'likes': Número de "me gusta" de la playlist.
                - 'n_videos': Duración de la playlist en formato 'HH:MM:SS'.
                - 'video_ids': IDs de los videos de la playlist
        """
        # Verificar si la API de YouTube está habilitada
        if not self.is_enabled():
            logger.warning('La API de YouTube no está habilitada. Saliendo de la función fetch_video_data.')
            return {}
        
        # Si no se le da un ID de canal salgo de la ejecucion
        if not playlist_id:
            raise ValueError('Se necesita un ID de video para obtener información en la función fetch_video_data().')
        
        # Inicializar el diccionario de datos
        data = {}
        
        try:
            # Realizar una solicitud para obtener los datos de la playlist desde la API de YouTube
            self.request = self.youtube.playlists().list(
                part='contentDetails,id,snippet',
                id=playlist_id,
            )
            response = self.execute()
            
            # Obtener los datos del video si la respuesta es válida
            if 'items' in response and response['items']:
                item = response['items'][0]
                
                # Obtener el ID del video
                data['playlist_id'] = item.get('id', playlist_id) 
                data['publish_date'] = item['snippet']['publishedAt']
                data['channel_id'] = item['snippet']['channelId']
                data['channel_name'] = item['snippet']['channelTitle']
                data['title'] = item['snippet']['title']
                data['views'] = 0
                data['likes'] = 0
                data['n_videos'] = item['contentDetails']['itemCount']
                data['video_ids'] = self.fetch_playlist_videos(playlist_id=playlist_id)

                logger.info(data)
            
        except Exception as e:
            logger.error(f'Se produjo un error al obtener la información para la playlist {playlist_id}. Error: {e}')
        
        # Placeholder para el tiempo medio de visualización de la playlist (actualmente no implementado)
        data['mvm'] = '00:00:00'
        
        return data

if __name__ == '__main__':
    # Ejemplo de uso
    youtube_api = YoutubeAPI()