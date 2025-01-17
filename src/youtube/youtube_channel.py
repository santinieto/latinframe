# Imports estándar de Python
import os
# import sys

# # Añade el directorio raíz del proyecto a sys.path
# current_path = os.path.dirname(os.path.abspath(__file__))
# project_root = os.path.abspath(os.path.join(current_path, '..', '..'))  # Ajusta según la estructura de tu proyecto
# sys.path.append(project_root)

# Imports de terceros
import re
import json
from bs4 import BeautifulSoup

# Imports locales
from src.utils.utils import get_http_response, get_formatted_date, clean_and_parse_number, getenv, is_video_online, fetch_excluded_ids
from src.logger.logger import Logger
from src.youtube.youtube_api import YoutubeAPI
from src.database.db import Database

################################################################################
# Genero una instancia del Logger
################################################################################
logger = Logger(os.path.basename(__file__)).get_logger()

class YoutubeChannel:
    ############################################################################
    # Metodos de incializacion
    ############################################################################
    # Valores por defecto para los atributos de la clase
    DEBUG = False
    DEFAULT_SAVE_HTML = False
    DEFAULT_N_VIDEOS_FETCH = 10
    DEFAULT_N_PLAYLISTS_FETCH = 10
    DEFAULT_N_SHORTS_FETCH = 10
    DEFAULT_FETCH_VIDEOS = True
    DEFAULT_FETCH_PLAYLISTS = True
    DEFAULT_FETCH_SHORTS = True
    DEFAULT_VALUES = {
        'channel_id': None,
        'channel_name': '',
        'channel_url': '',
        'publish_date': '',
        'country': '',
        'main_playlist': '',
        'channel_views': 0,
        'n_videos': 0,
        'subscribers': 0,
        'daily_subs': 0,
        'monthly_subs': 0,
        'video_id_list': [],
        'videos': [], # Aca se guardan los objetos de tipo YoutubeVideo
        'subchannels': [],
        'playlist_id_list': [],
        'playlists': [], # Aca se guardan los objetos de tipo YoutubePlaylist
        'short_id_list': [],
        'shorts': [], # Aca se guardan los objetos de tipo YoutubeShort
    }

    def __init__(self, channel_id=None, info_dict=None):
        # Inicialización de la clase
        
        # Establece los valores por defecto
        self.set_default_values()
        self.data_loaded = False
        self.html_content = None
        self.fetch_status = False
        self.save_html = getenv('YOUTUBE_CHANNEL_SAVE_HTML', self.DEFAULT_SAVE_HTML)
        self.fetch_channel_videos = getenv('YOUTUBE_CHANNEL_FETCH_VIDEOS', self.DEFAULT_FETCH_VIDEOS)
        self.fetch_channel_playlists = getenv('YOUTUBE_CHANNEL_FETCH_PLAYLISTS', self.DEFAULT_FETCH_PLAYLISTS)
        self.fetch_channel_shorts = getenv('YOUTUBE_CHANNEL_FETCH_SHORTS', self.DEFAULT_FETCH_SHORTS)
        self.n_videos_fetch = getenv('YOUTUBE_CHANNEL_N_VIDEOS_FETCH', self.DEFAULT_N_VIDEOS_FETCH)
        self.n_playlists_fetch = getenv('YOUTUBE_CHANNEL_N_PLAYLISTS_FETCH', self.DEFAULT_N_PLAYLISTS_FETCH)
        self.n_shorts_fetch = getenv('YOUTUBE_CHANNEL_N_SHORTS_FETCH', self.DEFAULT_N_SHORTS_FETCH)
        
        # Comprobaciones de seguridad
        self.n_videos_fetch = max(self.n_videos_fetch, 0) # Me aseguro que no sea menor que 0
        
        # Lista final de IDs de videos
        # Ya lo hago en set_default_values() pero no importa
        self.video_id_list = []
        
        # Limpio las listas internas de IDs
        self.video_ids_list_db = []
        self.video_ids_list_constructor = []
        self.video_ids_list_others = []
        self.video_ids_list_not_in_db = []

        # Prioridad de fuentes de IDs
        self.priority_order = ['not_in_db', 'database', 'others', 'constructor']
        
        # Si al momento de la creacion del objeto, el usuario
        # le da un ID de canal a la clase, lo uso
        if channel_id is not None:
            self.channel_id = channel_id

        # Si hay un diccionario para cargar datos, lo uso
        if info_dict:
            # Carga los valores desde un diccionario si se proporciona
            self.load_from_dict(info_dict)
        
        if self.channel_id:
            # Obtengo la lista de IDs excluidos
            self.excluded_video_ids = fetch_excluded_ids(f'{self.channel_id}_video', 'get')
            self.excluded_short_ids = fetch_excluded_ids(f'{self.channel_id}_short', 'get')
            self.excluded_playlist_ids = fetch_excluded_ids(f'{self.channel_id}_playlist', 'get')
                
            if self.DEBUG:
                logger.info(f'Lista de videos excluidos para el canal [{self.channel_id}]: {self.excluded_video_ids}')
                logger.info(f'Lista de shorts excluidos para el canal [{self.channel_id}]: {self.excluded_short_ids}')
                logger.info(f'Lista de playlists excluidos para el canal [{self.channel_id}]: {self.excluded_playlist_ids}')
        else:
            self.excluded_video_ids = []
            self.excluded_short_ids = []
            self.excluded_playlist_ids = []

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
        if 'channel_id' not in info_dict:
            # Registra un mensaje de error y sale si no se proporciona el campo 'channel_id'
            logger.error("El campo 'channel_id' no está presente en el diccionario de entrada.")
            return
        
        for key, value in info_dict.items():
            # Verifica si el atributo existe en la clase antes de establecer su valor
            if hasattr(self, key):
                # Establece el valor del atributo si existe en la clase
                setattr(self, key, value)
            else:
                # Mensaje de advertencia si la clave no es válida
                logger.warning(f"No se encontro el campo {key} para asignar el valor del atributo de YoutubeChannel")
            
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
            f"- ID del canal de YouTube: {self.channel_id}\n"
            f"- Nombre del canal de YouTube: {self.channel_name}\n"
            f"- Vistas del canal de YouTube: {self.channel_views}\n"
            f"- Número de videos del canal de YouTube: {self.n_videos}\n"
            f"- URL personalizada del canal de YouTube: {self.channel_url}\n"
            f"- Lista de reproducción principal del canal de YouTube: {self.main_playlist}\n"
            f"- Fecha de publicación del canal de YouTube: {self.publish_date}\n"
            f"- País del canal de YouTube: {self.country}\n"
            f"- Suscriptores del canal de YouTube: {self.subscribers}\n"
            f"- Suscriptores mensuales del canal de YouTube: {self.monthly_subs}\n"
            f"- Suscriptores diarios del canal de YouTube: {self.daily_subs}\n"
            f"- Lista de IDs de video del canal de YouTube: {self.video_id_list}\n"
            f"- Subcanales del canal de YouTube: {self.subchannels}\n"
            f"- Cantidad de playlists a buscar: {self.n_playlists_fetch}\n"
            f"- Listas de reproducción del canal de YouTube: {self.playlist_id_list}\n"
            f"- Cantidad de shorts a buscar: {self.n_shorts_fetch}\n"
            f"- Shorts del canal de YouTube: {self.short_id_list}\n"
        )
        return info_str

    ############################################################################
    # Funciones de obtencion de codigo HTML
    ############################################################################
    def set_html(self, html_content):
        """
        Establece el contenido HTML del canal de YouTube.

        Args:
            html_content (str): Contenido HTML a establecer.
        """
        self.html_content = html_content
        logger.info(f"Contenido HTML establecido con éxito para el canal [{self.channel_id}].")
        
    def fetch_html_content(self, url_type='id', ovr_id=None, scrap_url=None):
        """ 
        Obtiene el contenido HTML del canal de YouTube dado.

        Args:
            url_type (str): Tipo de URL a utilizar ('id', 'name' o 'url').
            ovr_id (str): ID del canal a usar en lugar del atributo actual.
            scrap_url (str): URL personalizada para hacer scraping.
        """
        # Si se proporciona un ID de canal para sobrescribir, úsalo
        if ovr_id is not None:
            logger.warning(f"Se va a cambiar el ID del canal [{self.channel_id}] por {ovr_id}")
            self.channel_id = ovr_id
            
        # Define una URL por defecto para hacer scraping
        if scrap_url is None:
            scrap_url = 'https://www.youtube.com/channel'

        # Construye la URL del canal de YouTube según el tipo
        if url_type == 'name':
            scrap_url = f'https://www.youtube.com/@{self.channel_name}'
        elif url_type == 'id':
            scrap_url = f'https://www.youtube.com/channel/{self.channel_id}'
        elif url_type == 'url':
            scrap_url = scrap_url
        else:
            logger.error("Tipo de URL no válido o scrap_url no proporcionado para 'url'.")
            return

        # Obtiene el contenido HTML
        self.html_content = get_http_response(scrap_url, response_type = 'text')
        
        # Busco el ID del canal si no lo tengo
        if not self.channel_id:
            # Transformo a un objeto de BeautifoulSoup
            response = BeautifulSoup(self.html_content, 'html.parser')
            # Busco la etiqueta <link> que tenga el atributo rel="canonical"
            elemento_link = response.find('link', rel='canonical')
            # Obtengo el link
            href = elemento_link.get('href')
            # Me quedo con el ID del canal
            self.channel_id = href.split('/')[-1]
        
        if self.html_content is None:
            logger.error(f"No se pudo obtener el contenido HTML para el canal [{self.channel_id}].")

    def save_html_content(self, html_content=None):
        """
        Guarda el contenido HTML del canal en un archivo.

        Args:
            html_content (str, optional): Contenido HTML a guardar. Si no se proporciona, se utiliza el contenido HTML del objeto.
        """
        try:
            # Si no se proporciona html_content, usa el contenido HTML del objeto
            if html_content is None:
                html_content = self.html_content
            
            # Genera el nombre del archivo con el ID del canal y la fecha actual
            channel_id = self.channel_id
            current_date = get_formatted_date()
            filename = f'html_channel_{channel_id}_{current_date}.html'
            
            # Directorio donde se guardarán los archivos HTML
            filepath = os.path.join(os.environ.get("SOFT_RESULTS", ''), 'channels')
            
            # Crea el directorio si no existe
            os.makedirs(filepath, exist_ok=True)
            
            # Ruta completa del archivo
            filepath = os.path.join(filepath, filename)

            # Guarda el contenido HTML en el archivo
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(html_content)
            
            logger.info(f"Contenido HTML para el canal {channel_id} guardado correctamente en: {filepath}")
        
        except Exception as e:
            logger.error(f"No se pudo guardar el contenido HTML para el canal {channel_id}. Error: {e}")

    ############################################################################
    # Obtencion de datos auxiliares
    ############################################################################
    def fetch_channel_aux_data(self):
        """
        Obtiene estadísticas del canal de YouTube mediante scraping de contenido HTML.

        Returns:
            dict: Diccionario con las estadísticas obtenidas.
        """
        # URL para obtener datos del canal
        url = f'https://socialcounts.org/youtube-live-subscriber-count/{self.channel_id}'

        # Obtener la respuesta HTTP
        response = get_http_response(url)

        # Manejo de errores si no se obtiene una respuesta
        if response is False:
            logger.error("Error al obtener la respuesta HTTP.")
            return False, {}

        # Inicializar el diccionario de estadísticas
        stats = {}

        # Obtener la cantidad de suscriptores
        try:
            stats['subscribers'] = response.find(
                class_='id_odometer__dDC1d mainOdometer'
            ).text
        except Exception as e:
            logger.warning(f"Fallo al obtener la cantidad de suscriptores para el canal [{self.channel_id}]. Error: {e}\nURL: {url}")
            stats['subscribers'] = self.DEFAULT_VALUES['subscribers']

        # Obtengo el resto de la informacion
        try:
            info = response.find_all(
                class_='id_main_profile__Vlbht id_odometer2__DYVeW'
            )
        except Exception as e:
            logger.error(f"Fallo al obtener la información adicional para el canal [{self.channel_id}]. Error: {e}\nURL: {url}")
            return False, {}

        # Obtener el resto de las estadísticas
        try:
            stats['channel_views'] = clean_and_parse_number(info[0].text.replace('Channel Views', ''))
        except Exception as e:
            logger.warning(f"Fallo al obtener las vistas para el canal [{self.channel_id}]. Error: {e}\nURL: {url}")
            stats['channel_views'] = self.DEFAULT_VALUES['channel_views']

        try:
            stats['n_videos'] = clean_and_parse_number(info[1].text.replace('Videos', ''))
        except Exception as e:
            logger.warning(f"Fallo al obtener el número de videos para el canal [{self.channel_id}]. Error: {e}\nURL: {url}")
            stats['n_videos'] = self.DEFAULT_VALUES['n_videos']

        try:
            stats['daily_subs'] = clean_and_parse_number(info[2].text.replace('Daily sub ', ''))
        except Exception as e:
            logger.warning(f"Fallo al obtener las suscripciones diarias para el canal [{self.channel_id}]. Error: {e}\nURL: {url}")
            stats['daily_subs'] = self.DEFAULT_VALUES['daily_subs']

        try:
            stats['monthly_subs'] = clean_and_parse_number(info[3].text.replace('Monthly sub ', ''))
        except Exception as e:
            logger.warning(f"Fallo al obtener las suscripciones mensuales para el canal [{self.channel_id}]. Error: {e}\nURL: {url}")
            stats['monthly_subs'] = self.DEFAULT_VALUES['monthly_subs']
            
        return True, stats
    
    def _fetch_channel_subchannels(self):
        """
        Obtiene las suscripciones (subcanales) de un canal de YouTube.
        
        Returns:
            list: Lista de tuplas (browse_id, canonical_base_url) que representan los subcanales.
        """
        try:
            # Construir la URL para obtener las suscripciones del canal
            url = f'https://www.youtube.com/channel/{self.channel_id}/channels'
            
            # Obtener el contenido HTML de la URL
            tmp_html_content = get_http_response(url, response_type='text')

            # Expresión regular para buscar browseEndpoint
            regex = r'"browseEndpoint":{[^{}]*?}'
            matches = re.findall(regex, tmp_html_content)
            
            # Crear una lista para almacenar los subcanales
            subchannels = []

            # Procesar las coincidencias
            for match in matches:
                # Parsear el JSON encontrado en la coincidencia
                data = json.loads("{" + match + "}")

                # Verificar si el objeto tiene tanto 'browseId' como 'canonicalBaseUrl'
                if "browseEndpoint" in data and "browseId" in data["browseEndpoint"] and "canonicalBaseUrl" in data["browseEndpoint"]:
                    # Extraer el valor de 'browseId'
                    browse_id = data["browseEndpoint"]["browseId"]

                    # Extraer el valor de 'canonicalBaseUrl'
                    canonical_base_url = data["browseEndpoint"]["canonicalBaseUrl"]

                    # Agregar una tupla con los valores al resultado
                    # Un canal no se agrega a sí mismo como subcanal
                    if browse_id != self.channel_id:
                        subchannels.append((browse_id, canonical_base_url))

            # Eliminar duplicados y devolver la lista de subcanales
            return list(set(subchannels))
        
        except Exception as e:
            # Registrar el error y devolver una lista vacía en caso de fallo
            logger.error(f"No se pudieron obtener las suscripciones del canal [{self.channel_id}]. Error: {e}")
            return []

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
                
            # Si hubo un fallo al obtener el codigo HTML del canal, logeo un
            # error y salgo de la funcion
            if self.html_content in [False, None]:
                logger.error(f"No se dispone de contenido HTML para el canal [{self.channel_id}].")
                return False
                
            if self.save_html:
                self.save_html_content()
            
            # Crear el diccionario para los datos
            channel_data = {
                'channel_id': self.channel_id, # Tiene que estar siempre este campo
                'channel_name': self._fetch_channel_name(),
                'channel_url': self._fetch_channel_custom_url(),
                'main_playlist': self.channel_id.replace("UC", "UU", 1),
                'subchannels': [x[0] for x in self._fetch_channel_subchannels()]
                }
                    
            # Obtengo los datos que me faltan
            status, aux_data = self.fetch_channel_aux_data()
    
            # Obtengo las listas de reproduccion si es requerido
            if self.fetch_channel_videos:
                channel_data['video_id_list'] = self._fetch_channel_video_ids()
    
            # Obtengo las listas de reproduccion si es requerido
            if self.fetch_channel_playlists:
                channel_data['playlist_id_list'] = self._fetch_channel_playlists()
    
            # Obtengo las listas de shorts si es requerido
            if self.fetch_channel_shorts:
                channel_data['short_id_list'] = self._fetch_channel_shorts()
            
            # Si se pudieron obtener los datos los agrego
            if status:
                channel_data['daily_subs'] = int(aux_data['daily_subs'])
                channel_data['monthly_subs'] = int(aux_data['monthly_subs'])
                channel_data['channel_views'] = int(aux_data['channel_views'])
                channel_data['n_videos'] = int(aux_data['n_videos'])
                channel_data['subscribers'] = int(aux_data['subscribers'])
            else:
                logger.warning(f'Se produjo un error al obtener los datos auxiliares para el canal [{self.channel_id}].')

            # Actualiza la información del canal con los datos obtenidos del scraping
            self.load_from_dict(channel_data)
            
            # Mensaje de debug
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
            logger.error(f"Fallo al aplicar el patrón de búsqueda {e} para el canal [{self.channel_id}].")
        except AttributeError as e:
            logger.error(f"Error de atributo {e} al obtener los datos para el patron {pattern} para el canal [{self.channel_id}].")
        except Exception as e:
            logger.error(f"Error inesperado al obtener los datos para el patron {pattern} para el canal [{self.channel_id}].")
        return None

    def _fetch_channel_name(self, pattern=None):
        """Obtiene el nombre del canal utilizando un patrón."""
        # Usar un patrón predeterminado si no se proporciona uno personalizado
        # pattern = r'"canonicalBaseUrl":"(.*?)"' if pattern is None else pattern
        pattern = r'{"channelMetadataRenderer":{"title":"(.*?)"' if pattern is None else pattern

        # Obtener la información requerida utilizando el método clásico
        channel_name = self._fetch_data_from_pattern(pattern, self.html_content)
        if channel_name:
            channel_name = channel_name.replace('/@','')
        else:
            channel_name = self.DEFAULT_VALUES['channel_name'] # Establecer un título predeterminado

        return channel_name

    def _fetch_channel_custom_url(self, pattern=None):
        """Obtiene el URL del canal utilizando un patrón."""
        # Usar un patrón predeterminado si no se proporciona uno personalizado
        pattern = r'"canonicalBaseUrl":"(.*?)"' if pattern is None else pattern

        # Obtener la información requerida utilizando el método clásico
        channel_url = self._fetch_data_from_pattern(pattern, self.html_content)
        if not channel_url:
            channel_url = self.DEFAULT_VALUES['channel_url']  # Establecer un título predeterminado

        return channel_url

    def _fetch_channel_video_ids(self, pattern=None):
        """
        Obtiene la lista de IDs de videos subidos por el canal de YouTube.
        
        Args:
            pattern (str): Patrón de expresión regular para buscar los IDs de videos. 
                            Por defecto, se utiliza el patrón predeterminado.
        
        Returns:
            list: Lista de IDs de videos subidos.
        """
        # Utiliza un patrón predeterminado si no se proporciona uno personalizado
        pattern = r'"videoId":"(.*?)"' if pattern is None else pattern
        
        try:
            # Realiza la búsqueda de los IDs de videos en el contenido HTML
            video_id_list = re.findall(pattern, self.html_content)
            
            self.add_video_ids_to_list(video_id_list, 'class')
            
            if self.DEBUG:
                logger.info(f"Lista de IDs de videos obtenida con éxito mediante contenido HTML para el canal [{self.channel_id}].")
        except Exception as e:
            # Si ocurre un error, registra el mensaje de error y establece la lista de IDs como vacía
            self.video_id_list = []
            logger.error(f"No se pudo obtener la lista de IDs de videos para el canal [{self.channel_id}]. Error: {e}")
        
        return self.DEFAULT_VALUES['video_id_list']
    
    def _fetch_channel_playlists(self):
        """
        Obtiene las listas de reproduccion de un canal de YouTube.
        
        Returns:
            list: Lista los ID de las listas de reproduccion para un canal.
        """
        try:
            # Construir la URL para obtener las suscripciones del canal
            url = f'https://www.youtube.com/channel/{self.channel_id}/playlists'
            
            # Obtener el contenido HTML de la URL
            tmp_html_content = get_http_response(url, response_type='text')
        
            # Guardo el contenido HTML
            # self.save_html_content(tmp_html_content)

            # Expresión regular para buscar browseEndpoint
            regex = r'"playlistId":"(.*?)"'
            matches = re.findall(regex, tmp_html_content)
            
            # Obtengo las playlists que estan en la base de datos
            with Database() as db:
                query = 'SELECT DISTINCT PLAYLIST_ID FROM PLAYLIST WHERE CHANNEL_ID = "{}"'.format(self.channel_id)
                results = db.select(query,())
                if results:
                    db_playlist_ids = set(x[0] for x in results)
                    if self.DEBUG:
                        logger.info('Playlists en la base de datos: {}'.format(db_playlist_ids))
                else:
                    db_playlist_ids = set()
        
            # Elimino duplicados y convierto a lista para mantener el orden original
            matches = list(dict.fromkeys(matches))
            
            # Encuentro las playlists que no están en la base de datos
            new_playlists = [p for p in matches if p not in db_playlist_ids]
            old_playlists = [p for p in matches if p     in db_playlist_ids]
            
            # Elimino los IDs que estan en la lista de excluidos
            filtered_new_playlists = [x for x in new_playlists if x not in self.excluded_playlist_ids]
            filtered_old_playlists = [x for x in old_playlists if x not in self.excluded_playlist_ids]
            
            # FIXME: Aca deberia incluir las playlists que tienen fallas en la
            # base de datos
            # Filtro los shorts que no estan online
            # online_shorts = [x for x in shorts_ids if is_video_online(x)]
            
            # # Los shorts que no estan disponibles los agrego a una base de datos
            # no_online_shorts = [x for x in shorts_ids if x not in online_shorts]
            # fetch_excluded_ids(f'{self.channel_id}_short', 'add', no_online_shorts)
            
            # Añado las playlists de la base de datos al final de la lista
            final_playlist_ids = filtered_new_playlists + filtered_old_playlists
            
            # Limito la cantidad de playlists si es necesario
            if len(final_playlist_ids) > self.n_playlists_fetch:
                final_playlist_ids = final_playlist_ids[:self.n_playlists_fetch]
            
            # Devuelvo el resultado sin repeticiones
            return final_playlist_ids
        
        except Exception as e:
            # Registrar el error y devolver una lista vacía en caso de fallo
            logger.error(f"No se pudieron obtener las listas de reproduccion del canal [{self.channel_id}]: {e}")
            return self.DEFAULT_VALUES['playlist_id_list']
    
    def _fetch_channel_shorts(self):
        """
        Obtiene los shorts de un canal de YouTube.
        
        Returns:
            list: Lista los ID de los shorts de reproduccion para un canal.
        """
        try:
            # Construir la URL para obtener las suscripciones del canal
            url = f'https://www.youtube.com/channel/{self.channel_id}/shorts'
            
            # Obtener el contenido HTML de la URL
            tmp_html_content = get_http_response(url, response_type='text')
        
            # Guardo el contenido HTML
            # self.save_html_content(tmp_html_content)
            
            # Obtengo los shorts que estan en la base de datos
            with Database() as db:
                query = 'SELECT DISTINCT SHORT_ID FROM SHORT WHERE CHANNEL_ID = "{}"'.format(self.channel_id)
                results = db.select(query,())
                if results:
                    db_short_ids = set(x[0] for x in results)
                    if self.DEBUG:
                        logger.info('Shorts en la base de datos: {}'.format(db_short_ids))
                else:
                    db_short_ids = set()
            
            # Expresión regular para buscar browseEndpoint
            regex = r'"videoId":"(.*?)"'
            matches = re.findall(regex, tmp_html_content)
            
            # Elimino duplicados y conformo la lista final
            matches = list(dict.fromkeys(matches))
            
            # Defino cuales son nuevos y cuales viejos
            new_short_ids = [x for x in matches if x not in db_short_ids]
            old_short_ids = [x for x in matches if x     in db_short_ids]
        
            # Elimino los IDs que estan en la lista de excluidos
            filtered_new_short_ids = [x for x in new_short_ids if x not in self.excluded_short_ids]
            filtered_old_short_ids = [x for x in old_short_ids if x not in self.excluded_short_ids]
            
            # Filtro los shorts que no estan online
            new_online_shorts = [x for x in filtered_new_short_ids if is_video_online(x)]
            old_online_shorts = [x for x in filtered_old_short_ids if is_video_online(x)]
            
            # Los shorts que no estan disponibles los agrego a una base de datos
            no_online_shorts = [x for x in filtered_new_short_ids if x not in new_online_shorts] + [x for x in filtered_old_short_ids if x not in old_online_shorts]
            if no_online_shorts:
                fetch_excluded_ids(f'{self.channel_id}_short', 'add', no_online_shorts)
                logger.info(f'Los siguientes shorts del canal [{self.channel_id}] no estan online y van a ser excluidos: {no_online_shorts}.')
            
            # Armo la lista de IDs final
            final_short_ids = new_online_shorts + old_online_shorts
            
            # Limito la cantidad de shorts
            if len(final_short_ids) > self.n_shorts_fetch:
                final_short_ids = final_short_ids[:self.n_shorts_fetch]
            
            # Devuelvo el resultado
            return final_short_ids
        
        except Exception as e:
            # Registrar el error y devolver una lista vacía en caso de fallo
            logger.error(f"No se pudieron obtener las listas de reproduccion del canal [{self.channel_id}]: {e}")
            return self.DEFAULT_VALUES['short_id_list']

    ############################################################################
    # Obtencion de datos mediante la API de Youtube
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
                # Intento obtener los datos para el canal
                channel_data = youtube_api.fetch_channel_data(self.channel_id)

                # Si la última petición a la API fue exitosa, cargo los datos
                if youtube_api.last_request_success:
                    
                    # Obtengo los datos que me faltan
                    status, aux_data = self.fetch_channel_aux_data()
                    
                    # Si se pudieron obtener los datos los agrego
                    if status:
                        channel_data['daily_subs'] = int(aux_data['daily_subs'])
                        channel_data['monthly_subs'] = int(aux_data['monthly_subs'])
                    else:
                        logger.warning(f'Se produjo un error al obtener los datos auxiliares para el canal [{self.channel_id}].')
                    
                    # Obtengo las suscripciones del canal en cuestion
                    channel_data['subchannels'] = [x[0] for x in self._fetch_channel_subchannels()]
    
                    # Obtengo las listas de reproduccion si es requerido
                    # NOTA: Para este caso, sobreescribo la lista que me
                    #    devuelve la API. El scrap me devuelve mas listas
                    #    que lo que me da la API
                    if self.fetch_channel_playlists:
                        channel_data['playlist_id_list'] = self._fetch_channel_playlists()
            
                    # Obtengo las listas de shorts si es requerido
                    if self.fetch_channel_shorts:
                        channel_data['short_id_list'] = self._fetch_channel_shorts()
                    
                    # Actualizo la informacion del canal
                    self.load_from_dict(channel_data)
                    
                    # Mensaje de debug
                    if self.DEBUG:
                        logger.info("Los datos se cargaron exitosamente utilizando la API de YouTube.")
                    return True
                
                else:
                    if self.DEBUG:
                        logger.debug(f"Se intento usar la API de YouTube para obtener los datos del canal [{self.channel_id}] pero hubo un fallo al procesar la peticion.")
            else:
                if self.DEBUG:
                    logger.debug(f"Se intento usar la API de YouTube para obtener los datos del canal [{self.channel_id}] pero la API esta deshabilitada.")
            
        except Exception as e:
            logger.warning(f"Fallo al cargar datos utilizando la API de YouTube: {e}")

        return False

    ############################################################################
    # Actualizar los datos del canal
    ############################################################################
    def fetch_data(self, info_dict=None, force_method=None):
        """
        Intenta cargar datos del canal de YouTube utilizando diferentes métodos.

        El orden de preferencia para cargar los datos es el siguiente:
        1. Datos proporcionados durante la inicialización del objeto.
        2. Utilización de la API de YouTube.
        3. Scraping de contenido HTML.

        Si alguno de los métodos falla, se pasará automáticamente al siguiente método.

        Args:
            info_dict (dict): Diccionario con datos del canal para cargar.
            force_method (str): Método para forzar la carga de datos ('api' para API de YouTube, 'html' para scraping HTML).

        Returns:
            bool: True si se cargaron los datos con éxito, False en caso contrario.
        """
        # Verifica si los datos ya están cargados
        if self.data_loaded:
            logger.info(f"Los datos del canal [{self.channel_id}] ya están cargados en el objeto YoutubeChannel.")
            self.fetch_status = True
            return

        # Intenta cargar datos del diccionario proporcionado durante la inicialización
        if info_dict:
            self.load_from_dict(info_dict)
            logger.info(f"Los datos del canal [{self.channel_id}] se cargaron exitosamente desde el diccionario proporcionado durante la inicialización.")
            self.fetch_status = True
            return

        # Verifica si se especificó un método forzado
        if force_method:
            logger.info(f"Los datos del canal [{self.channel_id}] se van a cargar forzadamente usando el metodo {force_method}.")
            
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
            
            logger.error(f"No se pudo cargar datos del canal [{self.channel_id}] de YouTube usando metodos forzados.")
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
        logger.error(f"No se pudo cargar datos del canal [{self.channel_id}] de YouTube.")
        self.fetch_status = False
        return

    def add_video_ids_to_list(self, new_video_ids, source = 'constructor'):
        """
        Añade una lista de IDs de video o un único ID de video a la lista existente, respetando el límite máximo de videos y evitando duplicados.

        Args:
        - new_video_ids: Una lista de IDs de video o un único ID de video a añadir.
        - source: El origen de los IDs (constructor, database, others)

        Usage:
        - Para añadir una lista de IDs de video:
            objeto_clase.add_video_ids_to_list(["video1", "video2", "video3"])
        
        - Para añadir un único ID de video:
            objeto_clase.add_video_ids_to_list("video4")
        """
        if isinstance(new_video_ids, str):
            new_video_ids = [new_video_ids]  # Convertir un solo ID de video en una lista
        elif not isinstance(new_video_ids, list):
            # Si new_video_ids no es una cadena o una lista, emitir un mensaje de advertencia y salir
            logger.warning(f"La entrada [{new_video_ids}] debe ser una cadena de caracteres o una lista. Tipo proporcionado: {type(new_video_ids)}")
            return
            
        # Elimino los IDs que estan en la lista de excluidos
        new_video_ids = [x for x in new_video_ids if x not in self.excluded_video_ids]
        
        # Filtro los videos que no estan online
        online_videos = [x for x in new_video_ids if is_video_online(x)]
        
        # Los videos que no estan disponibles los agrego a una base de datos
        no_online_videos = [x for x in new_video_ids if x not in online_videos]
        
        if no_online_videos:
            fetch_excluded_ids(f'{self.channel_id}_video', 'add', no_online_videos)
            logger.info(f'Los siguientes videos del canal [{self.channel_id}] de la fuente [{source}] no estan online y van a ser excluidos: {no_online_videos}.')
        
        # Defino el origen de los datos y los agrego a la lista correspondiente
        if source == 'database':
            self.video_ids_list_db.extend(online_videos)
        elif source == 'constructor':
            self.video_ids_list_constructor.extend(online_videos)
        else:
            self.video_ids_list_others.extend(online_videos)
        
        # Actualizar la lista de IDs que no están en la base de datos
        self.video_ids_list_not_in_db = [x for x in online_videos if x not in self.video_ids_list_db]
        
        # Muestro la lista de canales que no estan en la base de datos
        if self.DEBUG:
            logger.info(f'Lista de IDs que no estan en la base de datos para el canal [{self.channel_id}]: {self.video_ids_list_not_in_db}')

        # Actualizar la lista final de videos
        self.update_final_video_list()

    def update_final_video_list(self):
        """
        Construye la lista final de videos basada en la prioridad configurada.
        """
        all_videos = {
            'not_in_db': self.video_ids_list_not_in_db,
            'database': self.video_ids_list_db,
            'others': self.video_ids_list_others,
            'constructor': self.video_ids_list_constructor
        }

        total_video_ids_list = []
        for source in self.priority_order:
            total_video_ids_list.extend(all_videos[source])
        
        # Eliminar duplicados y mantener el orden original
        total_video_ids_list = list(dict.fromkeys(total_video_ids_list))
        
        # Cortar la lista total según el límite configurado
        self.video_id_list = total_video_ids_list[:self.n_videos_fetch]
        not_added_ids = total_video_ids_list[self.n_videos_fetch:]
        
        # Emitir un mensaje de advertencia con los IDs de video que no se pudieron agregar
        if self.DEBUG:
            logger.warning(f"No se pudieron agregar los siguientes IDs de video para el canal [{self.channel_id}] debido a que se alcanzó el límite máximo o ya están en la lista: {not_added_ids}")

    def set_priority_order(self, priority_order):
        """
        Establece un nuevo orden de prioridad para las fuentes de IDs.

        Args:
        - priority_order: Una lista con el nuevo orden de prioridad. Debe contener 'not_in_db', 'database', 'others' y 'constructor'.
        """
        if set(priority_order) == {'not_in_db', 'database', 'others', 'constructor'}:
            self.priority_order = priority_order
            self.update_final_video_list()
        else:
            logger.warning(f"El orden de prioridad proporcionado no es válido: {priority_order}")

if __name__ == "__main__":
    # Crear una instancia de YoutubeChannel
    channel = YoutubeChannel(channel_id='UCbCmjCuTUZos6Inko4u57UQ') # Cocomelon

    # Simular que los datos ya están cargados
    # Si esta en True se acaba la ejecucion del programa
    channel.data_loaded = False

    # Llamar al método fetch_data
    channel.fetch_data(force_method='html')
    success = channel.fetch_status

    # Verificar si se cargaron los datos con éxito
    if success:
        print("Los datos se cargaron con éxito.")
        print(str(channel))
    else:
        print("Error al cargar los datos.")