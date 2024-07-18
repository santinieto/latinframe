# Imports estándar de Python
import os
# import sys

# # Añade el directorio raíz del proyecto a sys.path
# current_path = os.path.dirname(os.path.abspath(__file__))
# project_root = os.path.abspath(os.path.join(current_path, '..', '..'))  # Ajusta según la estructura de tu proyecto
# sys.path.append(project_root)

# Imports de terceros
import re
import requests
import json
import datetime

# Imports locales
from src.utils.utils import get_http_response, get_formatted_date, getenv
from src.database.db import Database
from src.logger.logger import Logger
from src.youtube.youtube_api import YoutubeAPI

################################################################################
# Genero una instancia del Logger
################################################################################
logger = Logger(os.path.basename(__file__)).get_logger()

class YoutubePlaylist:
    ############################################################################
    # Metodos de incializacion
    ############################################################################
    # Valores por defecto para los atributos de la clase
    DEBUG = False
    DEFAULT_SAVE_HTML = True
    DEFAULT_VALUES = {
        'playlist_id': 'Unknown Playlist ID',
        'channel_id': 'Unknow Channel ID',
        'channel_name': 'Unknow Channel Name',
        'title': 'Unknown Title',
        'views': 0,
        'likes': 0,
        'n_videos': 0,
        'publish_date': "00/00/00",
        'video_ids': [],
    }
    
    def __init__(self, playlist_id=None, info_dict=None):
        # Inicialización de la clase
        self.set_default_values()
        self.data_loaded = False
        self.html_content = None
        self.fetch_status = False
        self.save_html = getenv('YOUTUBE_PLAYLIST_SAVE_HTML', self.DEFAULT_SAVE_HTML)
        
        # Si al momento de la creación del objeto se proporciona un ID de playlist, lo usamos
        if playlist_id is not None:
            self.playlist_id = playlist_id
        
        # Si hay un diccionario para cargar datos, lo usamos
        if info_dict:
            # Cargamos los valores desde un diccionario si se proporciona
            self.load_from_dict(info_dict)

    def set_default_values(self):
        """Establece los valores por defecto de los atributos de la clase."""
        for key, value in self.DEFAULT_VALUES.items():
            # Establece el valor por defecto para cada atributo de la clase
            setattr(self, key, value)

    def load_from_dict(self, info_dict):
        """
        Carga los valores de un diccionario en los atributos de la clase.

        Args:
            info_dict (dict): Diccionario con los valores a cargar.
        """
        if 'playlist_id' not in info_dict:
            # Registra un mensaje de error y sale si no se proporciona el campo 'playlist_id'
            logger.error("El campo 'playlist_id' no está presente en el diccionario de entrada.")
            return
        
        for key, value in info_dict.items():
            # Verifica si el atributo existe en la clase antes de establecer su valor
            if hasattr(self, key):
                # Establece el valor del atributo si existe en la clase
                setattr(self, key, value)
            else:
                # Mensaje de advertencia si la clave no es válida
                logger.warning(f"No se encontro el campo [{key}] para asignar el valor del atributo de YoutubePlaylist")
            
            # Levanto la bandera para indicar que el objeto tiene datos
            self.data_loaded = True

    def to_dict(self):
        """
        Convierte los atributos de la clase en un diccionario.

        Returns:
            dict: Diccionario con los valores de los atributos de la clase.
        """
        # Genera un diccionario con los valores de los atributos de la clase
        return {attr: getattr(self, attr) for attr in self.DEFAULT_VALUES.keys()}

    def __str__(self):
        """Devuelve todos los campos de la clase para ser mostrados en pantalla o en un archivo."""
        info_str = (
            f"- ID de la playlist de YouTube: {self.playlist_id}\n"
            f"- ID del canal de YouTube al que pertenece: {self.channel_id}\n"
            f"- Nombre del canal de YouTube al que pertenece: {self.channel_name}\n"
            f"- Título de la playlist de YouTube: {self.title}\n"
            f"- Vistas de la playlist de YouTube: {self.views}\n"
            f"- Cantidad de Me Gusta de la playlist de YouTube: {self.likes}\n"
            f"- Cantidad de videos en la playlist de YouTube: {self.n_videos}\n"
            f"- Fecha de publicación de la playlist de YouTube: {self.publish_date}\n"
            f"- Lista de IDs de los videos: {self.video_ids}"
        )
        return info_str
    
    ############################################################################
    # Funciones de obtención de contenido HTML
    ############################################################################
    def set_html(self, html_content):
        """
        Establece el contenido HTML de la playlist de YouTube.

        Args:
            html_content (str): Contenido HTML a establecer.
        """
        self.html_content = html_content
        if self.DEBUG:
            logger.info(f"Contenido HTML establecido con éxito para la playlist {self.playlist_id}.")
        
    def fetch_html_content(self, url_type='id', ovr_id=None, scrap_url=None):
        """ 
        Obtiene el contenido HTML de la playlist de YouTube dado.

        Args:
            url_type (str): Tipo de URL a utilizar ('id' o 'url').
            ovr_id (str): ID de la playlist a usar en lugar del atributo actual.
            scrap_url (str): URL personalizada para hacer scraping.
        """
        # Si se proporciona un ID de playlist para sobrescribir, úsalo
        if ovr_id is not None:
            logger.warning(f"Se va a cambiar el ID de la playlist {self.playlist_id} por {ovr_id}")
            self.playlist_id = ovr_id
            
        # Define una URL por defecto para hacer scraping
        if scrap_url is None:
            scrap_url = 'https://www.youtube.com/playlist?list='

        # Construye la URL de la playlist de YouTube según el tipo
        if url_type == 'id':
            scrap_url = f'https://www.youtube.com/playlist?list={self.playlist_id}'
        elif url_type == 'url':
            scrap_url = scrap_url
            # Expresión regular para extraer el valor del parámetro 'v'
            match = re.search(r'[?&]v=([^&]+)', scrap_url)
            if match:
                self.playlist_id = match.group(1)
        else:
            logger.error("Tipo de URL no válido o scrap_url no proporcionado para 'url'.")
            return

        # Obtiene el contenido HTML
        self.html_content = get_http_response(scrap_url, response_type='text')
        
        if self.html_content is None:
            logger.error(f"No se pudo obtener el contenido HTML para la playlist {self.playlist_id}.")

    def save_html_content(self, html_content=None):
        """
        Guarda el contenido HTML de la playlist en un archivo.

        Args:
            html_content (str, optional): Contenido HTML a guardar. Si no se proporciona, se utiliza el contenido HTML del objeto.
        """
        try:
            # Si no se proporciona html_content, usa el contenido HTML del objeto
            if html_content is None:
                html_content = self.html_content
            
            # Genera el nombre del archivo con el ID de la playlist y la fecha actual
            playlist_id = self.playlist_id
            current_date = get_formatted_date()
            filename = f'html_playlist_{playlist_id}_{current_date}.html'
            
            # Directorio donde se guardarán los archivos HTML
            filepath = os.path.join(os.environ.get("SOFT_RESULTS", ''), 'playlist')
            
            # Crea el directorio si no existe
            os.makedirs(filepath, exist_ok=True)
            
            # Ruta completa del archivo
            filepath = os.path.join(filepath, filename)

            # Guarda el contenido HTML en el archivo
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(html_content)
            
            logger.info(f"Contenido HTML para la playlist {playlist_id} guardado correctamente en: {filepath}")
        
        except Exception as e:
            logger.error(f"No se pudo guardar el contenido HTML para la playlist {playlist_id}. Error: {e}")

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

            # Si hubo un fallo al obtener el código HTML de la playlist, logeo un error y salgo de la función
            if self.html_content in [False, None]:
                logger.error(f"No se dispone de contenido HTML para la playlist {self.playlist_id}.")
                return False

            if self.save_html:
                self.save_html_content()

            # Crear el diccionario para los datos
            playlist_data = {
                'playlist_id': self.playlist_id,  # Tiene que estar siempre este campo
                'channel_name': self._fetch_channel_name(),
                'title': self._fetch_playlist_title(),
                'views': self._fetch_playlist_views(),
                'publish_date': self._fetch_publish_date(),
                'likes': self._fetch_playlist_likes(),
                'n_videos': self._fetch_n_videos(),
                'video_ids': self._fetch_video_ids(),
            }
            
            playlist_data['channel_id'] = self._fetch_channel_id(playlist_data['channel_name'])

            # Actualiza la información de la playlist con los datos obtenidos del scraping
            self.load_from_dict(playlist_data)
            if self.DEBUG:
                logger.info("Los datos se cargaron exitosamente mediante scraping de contenido HTML.")
            return True

        except Exception as e:
            logger.warning(f"Fallo al cargar datos mediante scraping de contenido HTML: {e}")

        return False

    def _fetch_data_from_pattern(self, pattern, html):
        """Obtiene datos del contenido HTML dado un patrón."""
        try:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
        except re.error as e:
            logger.error(f"Fallo al aplicar el patrón de búsqueda {e} para el canal {self.channel_id}.")
        except AttributeError as e:
            logger.error(f"Error de atributo {e} al obtener los datos para el patron {pattern} para el canal {self.channel_id}.")
        except Exception as e:
            logger.error(f"Error inesperado al obtener los datos para el patron {pattern} para el canal {self.channel_id}.")
        return None
    
    def _fetch_channel_id(self, channel_name=None):
        """
        Obtiene el ID del canal basado en el nombre del canal proporcionado.
        
        Parameters:
            channel_name (str): El nombre del canal para buscar su ID.
            
        Returns:
            str: El ID del canal. Si no se encuentra, devuelve el ID predeterminado.
        """
        # ID del canal predeterminado
        channel_id = self.DEFAULT_VALUES['channel_id']
        
        # Si no se proporciona un nombre de canal, devuelve el ID predeterminado
        if not channel_name:
            return channel_id
        
        # Aca falta algo para buscar el ID por otro lado
        # Si no se encuentra en la base de datos, podrías agregar una búsqueda adicional aquí
        
        # Obtengo el ID desde la base de datos
        with Database() as db:
            try:
                results = db.select(
                    'SELECT DISTINCT CHANNEL_ID FROM CHANNEL WHERE CHANNEL_NAME = "{}"'.format(channel_name),
                    ())
                
                # Si se encuentran resultados, actualiza el ID del canal
                if results:
                    channel_id = results[0][0]
            except Exception as e:
                logger.error(f'Error al obtener el ID del canal para el nombre [{channel_name}]. Error: {e}')
        
        # Devuelve el ID del canal (puede ser el predeterminado si no se encuentra)
        return channel_id
    
    def _fetch_channel_name(self, pattern=None):
        """Obtiene el nombre del canal de Youtube para la playlist a partir del contenido HTML.

        Args:
            pattern (str, opcional): Patrón de búsqueda para extraer el nombre del canal la playlist.

        Returns:
            str: Nombre del canal de Youtube.

        Notas:
            - Este método tiene un algoritmo principal y uno alternativo.
        """
        try:
            # Si no se proporciona un patrón, se utiliza uno predeterminado
            pattern = r'"ownerChannelName":"(.*?)"' if pattern is None else pattern

            # Intenta obtener el nombre del canal la playlist utilizando el patrón dado en el HTML
            channel_name = self._fetch_data_from_pattern(pattern, self.html_content)

            # Si se encuentra el nombre del canal la playlist, devolverlo
            if channel_name:
                return channel_name

            # Construir una URL alternativa para hacer scraping si el método principal falla
            url = f'https://www.youtube.com/oembed?url=http://www.youtube.com/playlist?list={self.playlist_id}&format=json'
            # Obtener la respuesta HTTP
            response = requests.get(url)
            # Transformar a datos JSON
            data = json.loads(response.text)
            # Obtener el título de la playlist
            channel_name = data['author_name']
            
            return channel_name

        except Exception as e:
            # Registra un mensaje de error si no se puede obtener el nombre del canal la playlist
            logger.error(f"No se pudo obtener el nombre del canal para la playlist [{self.playlist_id}]. Error: {str(e)}")

        # Establece un valor predeterminado de None si no se puede obtener el nombre del canal la playlist
        return self.DEFAULT_VALUES['channel_name']
    
    def _fetch_playlist_title(self, pattern=None):
        """ 
        Obtiene el título de la playlist utilizando un patrón sobre el contenido HTML cargado.
        Registra un error si no se puede obtener el título de la playlist.

        Args:
            pattern (opcional): Patrón de búsqueda para extraer el título de la playlist.

        Notas:
            - Este método tiene un algoritmo principal y uno alternativo.
            - El título de la playlist se establece como 'Unknown' si todo falla.
        """
        title = self.DEFAULT_VALUES['title']
        
        try:
            # Si se proporciona un patrón personalizado, úsalo, si no, usa uno predeterminado
            pattern = r'"title":"(.*?)"' if pattern is None else pattern

            # Obtener la información requerida utilizando el método clásico
            title = self._fetch_data_from_pattern(pattern, self.html_content)

            # Si se obtiene el título, devolverlo
            if title:
                return title

            # Construir una URL alternativa para hacer scraping si el método principal falla
            url = f'https://www.youtube.com/oembed?url=http://www.youtube.com/playlist?list={self.playlist_id}&format=json'
            # Obtener la respuesta HTTP
            response = requests.get(url)
            # Transformar a datos JSON
            data = json.loads(response.text)
            # Obtener el título de la playlist
            title = data['title']

            return title

        except re.error as e:
            logger.error(f"Fallo al aplicar el patrón de búsqueda {pattern} para el video [{self.playlist_id}].")
        except AttributeError as e:
            logger.error(f"Error de atributo {e} al obtener los datos para el patron {pattern} para el video [{self.playlist_id}].")
        except Exception as e:
            logger.error(f"Error inesperado al obtener el título para el video [{self.playlist_id}]: {str(e)}")
    
    def _fetch_playlist_views(self):
        """ 
        """
        views = self.DEFAULT_VALUES['views']
        
        try:
            # Obtengo la lista de videos presentes para la playlist en la base de datos
            with Database() as db:
                result = db.select(
                    '''
                    SELECT SUM(VR.VIEWS)
                    FROM VIDEO_RECORDS VR
                    WHERE VR.VIDEO_ID IN (
                        SELECT PV.VIDEO_ID
                        FROM PLAYLIST_VIDEO PV
                        WHERE PV.PLAYLIST_ID = "{}"
                    )
                    '''.format(self.playlist_id),
                    ())
                
                if result:
                    x = result[0][0]
                    return x if x is not None else self.DEFAULT_VALUES['views']
                    
        # Gestion de errores
        except Exception as e:
            logger.error(f"No se pudo obtener la cantidad de visualizaciones para la playlist {self.playlist_id}: {str(e)}")
        
        return views
    
    def _fetch_publish_date(self, pattern_1=None, pattern_2=None):
        """ 
        Obtiene la fecha de publicación de la playlist utilizando un patrón sobre el contenido HTML cargado.
        Registra un error si no se puede obtener la fecha de publicación de la playlist.

        Args:
            pattern_1 (opcional): Patrón de búsqueda 1 para extraer la fecha de publicación de la playlist.
            pattern_2 (opcional): Patrón de búsqueda 2 para extraer la fecha de publicación de la playlist.

        Notas:
            - Este método tiene un algoritmo principal y uno alternativo.
            - La fecha de publicación de la playlist se establece en '00/00/00' si todo falla.
        """
        publish_date = self.DEFAULT_VALUES['publish_date']
        
        try:
            # # Si se proporciona un patrón personalizado, úsalo, si no, usa uno predeterminado
            # pattern_1 = r'"uploadDate":"(.*?)"' if pattern_1 is None else pattern_1
            # pattern_2 = r'"publishDate":"(.*?)"' if pattern_2 is None else pattern_2

            # # Intentar obtener la fecha de publicación utilizando el primer patrón
            # publish_date = self._fetch_data_from_pattern(pattern_1, self.html_content)
            
            # # Si obtengo un resultado valido termino la ejecucion
            # if publish_date:
            #     # Convertir la cadena a un objeto datetime
            #     fecha_objeto = datetime.fromisoformat(publish_date)
            #     # Formatear la fecha en el nuevo formato
            #     publish_date = fecha_objeto.strftime("%Y-%m-%d %H:%M:%S")
            #     return publish_date

            # # Intentar obtener la fecha de publicación utilizando el segundo patrón si falla el primero
            # publish_date = self._fetch_data_from_pattern(pattern_2, self.html_content)
            
            # # Si obtengo un resultado valido termino la ejecucion
            # if publish_date:
            #     # Convertir la cadena a un objeto datetime
            #     fecha_objeto = datetime.fromisoformat(publish_date)
            #     # Formatear la fecha en el nuevo formato
            #     publish_date = fecha_objeto.strftime("%Y-%m-%d %H:%M:%S")
            #     return publish_date
            
            # Obtengo la fecha de puclicacion desde la base de datos
            with Database() as db:
                try:
                    results = db.select(
                        'SELECT PUBLISH_DATE FROM PLAYLIST WHERE PLAYLIST_ID = "{}" ORDER BY UPDATE_DATE DESC'.format(self.playlist_id),
                        ())
                    
                    # Si se encuentran resultados, actualiza el ID del canal
                    if results:
                        x = results[0][0]
                        publish_date = x if x is not None else self.DEFAULT_VALUES['publish_date']
                except Exception as e:
                    logger.error(f'Error al obtener la fecha de publicacion de la playlist [{self.playlist_id}]. Error: {e}')
                    
        # Gestion de errores
        except ValueError as e:
            logger.error(f"Fallo al intentar formatear la fecha de publicación para el video {self.video_id}. Error: {e}")
        except re.error as e:
            logger.error(f"Fallo al aplicar los patrones de búsqueda {pattern_1}, {pattern_2} para obtener la fecha de publicacion para el video {self.video_id}.")
        except Exception as e:
            logger.error(f"No se pudo obtener la fecha de publicación para el video {self.id}: {str(e)}")

        return publish_date
    
    def _fetch_playlist_likes(self):
        """ 
        """
        likes = self.DEFAULT_VALUES['likes']
        
        try:
            # Obtengo la lista de videos presentes para la playlist en la base de datos
            with Database() as db:
                record = db.select(
                    '''
                    SELECT SUM(VR.LIKES)
                    FROM VIDEO_RECORDS VR
                    WHERE VR.VIDEO_ID IN (
                        SELECT PV.VIDEO_ID
                        FROM PLAYLIST_VIDEO PV
                        WHERE PV.PLAYLIST_ID = "{}"
                    )
                    '''.format(self.playlist_id),
                    ())
                
                if record:
                    return record[0][0]
                else:
                    return 0
                    
        # Gestion de errores
        except Exception as e:
            logger.error(f"No se pudo obtener el recuento de Me Gusta para la playlist {self.playlist_id}: {str(e)}")

        return likes
    
    def _fetch_n_videos(self):
        """
        Obtiene el numero de videos de la playlist basado en registros anteriores.
        
        Parameters:
            channel_name (str): El nombre del canal para buscar su ID.
            
        Returns:
            str: El ID del canal. Si no se encuentra, devuelve el ID predeterminado.
        """
        # ID del canal predeterminado
        n_videos = self.DEFAULT_VALUES['n_videos']
        
        # Aca falta algo para buscar el ID por otro lado
        # Si no se encuentra en la base de datos, podrías agregar una búsqueda adicional aquí
        
        # Obtengo el ID desde la base de datos
        with Database() as db:
            try:
                results = db.select(
                    'SELECT VIDEOS_COUNT FROM PLAYLIST_RECORDS WHERE PLAYLIST_ID = "{}" ORDER BY UPDATE_DATE DESC'.format(self.playlist_id),
                    ())
                
                # Si se encuentran resultados, actualiza el ID del canal
                if results:
                    n_videos = results[0][0]
            except Exception as e:
                logger.error(f'Error al obtener la cantidad de videos de la playlist [{self.playlist_id}]. Error: {e}')
                
        return n_videos
    
    def _fetch_video_ids(self):
        return self.DEFAULT_VALUES['video_ids']
    
    ############################################################################
    # Obtención de datos mediante la API de YouTube
    ############################################################################
    def _load_data_from_api(self):
        """
        Intenta cargar datos utilizando la API de YouTube.

        Returns:
            bool: True si se cargaron los datos con éxito, False en caso contrario.
        """
        try:
            # Creo/Obtengo la instancia de la clase para la API de YouTube
            youtube_api = YoutubeAPI()

            # Si la API está habilitada,
            if youtube_api.is_enabled():
                # Intento obtener los datos para la playlist
                playlist_data = youtube_api.fetch_playlist_data(self.playlist_id)

                # Si la última petición a la API fue exitosa, cargo los datos
                if youtube_api.last_request_success:
                    
                    # Actualizo la información de la playlist
                    self.load_from_dict(playlist_data)
                    
                    playlist_data['views'] = self._fetch_playlist_views()
                    playlist_data['likes'] = self._fetch_playlist_likes()
                    
                    if self.DEBUG:
                        logger.info("Los datos se cargaron exitosamente utilizando la API de YouTube.")
                    return True
                
                else:
                    if self.DEBUG:
                        logger.debug(f"Se intentó usar la API de YouTube para obtener los datos de la playlist {self.playlist_id} pero hubo un fallo al procesar la petición.")
            else:
                if self.DEBUG:
                    logger.debug(f"Se intentó usar la API de YouTube para obtener los datos de la playlist {self.playlist_id} pero la API está deshabilitada.")
        
        except Exception as e:
            logger.warning(f"Fallo al cargar datos utilizando la API de YouTube: {e}")

        return False

    ############################################################################
    # Actualizar los datos de la playlist
    ############################################################################
    def fetch_data(self, info_dict=None, force_method=None):
        """
        Intenta cargar datos de la playlist de YouTube utilizando diferentes métodos.

        El orden de preferencia para cargar los datos es el siguiente:
        1. Datos proporcionados durante la inicialización del objeto.
        2. Utilización de la API de YouTube.
        3. Scraping de contenido HTML.

        Si alguno de los métodos falla, se pasará automáticamente al siguiente método.

        Args:
            info_dict (dict): Diccionario con datos de la playlist para cargar.
            force_method (str): Método para forzar la carga de datos ('api' para API de YouTube, 'html' para scraping HTML).

        Returns:
            bool: True si se cargaron los datos con éxito, False en caso contrario.
        """
        # Verifica si los datos ya están cargados
        if self.data_loaded:
            logger.info(f"Los datos de la playlist [{self.playlist_id}] ya están cargados en el objeto YoutubePlaylist.")
            self.fetch_status = True
            return

        # Intenta cargar datos del diccionario proporcionado durante la inicialización
        if info_dict:
            self.load_from_dict(info_dict)
            logger.info(f"Los datos de la playlist [{self.playlist_id}] se cargaron exitosamente desde el diccionario proporcionado durante la inicialización.")
            self.fetch_status = True
            return

        # Verifica si se especificó un método forzado
        if force_method:
            logger.info(f"Los datos de la playlist [{self.playlist_id}] se van a cargar forzadamente usando el método [{force_method}].")
            
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
            
            logger.error(f"No se pudo cargar datos de la playlist [{self.playlist_id}] de YouTube usando métodos forzados.")
            self.fetch_status = False
            return

        # Intenta cargar datos utilizando la API de YouTube si no se especifica un método forzado
        if self._load_data_from_api():
            self.fetch_status = True
            return

        # Intenta cargar datos mediante scraping de contenido HTML si no se especifica un método forzado
        if self._load_data_from_html():
            self.fetch_status = True
            return

        # Si no se pudo cargar datos de ninguna manera, registra un mensaje de error
        logger.error(f"No se pudo cargar datos de la playlist {self.playlist_id} de YouTube.")
        self.fetch_status = False
        return
    
if __name__ == "__main__":
    from src.utils.environment import set_environment
    set_environment('settings.json')
    
    # Crear una instancia de YoutubePlaylist
    playlist = YoutubePlaylist(playlist_id='PLT1rvk7Trkw6fwEkuMl_I5t1PLvxAytL5')
    # playlist = YoutubePlaylist(playlist_id='PLBRoHO-L7e4Iw_JjEw2IlpE_FeR-wzgPS')

    # Simular que los datos ya están cargados
    # Si está en True se acaba la ejecución del programa
    playlist.data_loaded = False

    # Llamar al método fetch_data
    playlist.fetch_data(force_method='html')

    # Verificar si se cargaron los datos con éxito
    if playlist.fetch_status:
        logger.info("Los datos se cargaron con éxito.")
        logger.info(str(playlist))
    else:
        logger.info("Error al cargar los datos.")
    
    # Guardo el playlist en la base da datos
    # from src.database.db import Database
    # with Database() as db:
    #     db.insert_playlist_record( playlist.to_dict() )