from src.utils.utils import get_http_response
from src.utils.utils import get_formatted_date
from src.utils.utils import clean_and_parse_number
from src.utils.utils import getenv
from src.utils.utils import get_time_len
from src.utils.logger import Logger
from src.youtube.youtube_api import YoutubeAPI
import os
import re
import json
import requests
from pytube import YouTube
from datetime import datetime
from bs4 import BeautifulSoup

# Crear un logger
logger = Logger().get_logger()

class YoutubeVideo:
    ############################################################################
    # Metodos de incializacion
    ############################################################################
    # Valores por defecto para los atributos de la clase
    DEBUG = True
    SAVE_HTML = getenv('YOUTUBE_VIDEO_SAVE_HTML', True)
    DEFAULT_VALUES = {
        'video_id': 'Unknown Video ID',
        'channel_id': 'Unknow Channel ID',
        'channel_name': 'Unknow Channel Name',
        'title': 'Unknown Title',
        'views': 0,
        'likes': 0,
        'length': '00:00:00',
        'comment_count': 0,
        'mvm': '00:00:00',
        'tags': "None",
        'publish_date': "00/00/00"
    }
    
    def __init__(self, video_id=None, info_dict=None):
        # Inicialización de la clase
        self.set_default_values()
        self.data_loaded = False
        self.html_content = None
        self.fetch_status = False
        
        # Si al momento de la creación del objeto se proporciona un ID de video, lo usamos
        if video_id is not None:
            self.video_id = video_id
        
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
        if 'video_id' not in info_dict:
            # Registra un mensaje de error y sale si no se proporciona el campo 'video_id'
            logger.error("El campo 'video_id' no está presente en el diccionario de entrada.")
            return
        
        for key, value in info_dict.items():
            # Verifica si el atributo existe en la clase antes de establecer su valor
            if hasattr(self, key):
                # Establece el valor del atributo si existe en la clase
                setattr(self, key, value)
            else:
                # Mensaje de advertencia si la clave no es válida
                logger.warning(f"No se encontro el campo [{key}] para asignar el valor del atributo de YoutubeVideo")
            
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
            f"- ID del video de YouTube: {self.video_id}\n"
            f"- ID del canal de YouTube al que pertenece: {self.channel_id}\n"
            f"- Nombre del canal de YouTube al que pertenece: {self.channel_name}\n"
            f"- Título del video de YouTube: {self.title}\n"
            f"- Vistas del video de YouTube: {self.views}\n"
            f"- Cantidad de Me Gusta del video de YouTube: {self.likes}\n"
            f"- Duración del video de YouTube: {self.length}\n"
            f"- Cantidad de comentarios del video de YouTube: {self.comment_count}\n"
            f"- Momento Mas Visto (MVM) del video de YouTube: {self.mvm}\n"
            f"- Tags del video de YouTube: {self.tags}\n"
            f"- Fecha de publicación del video de YouTube: {self.publish_date}"
        )
        return info_str
    
    ############################################################################
    # Funciones de obtención de contenido HTML
    ############################################################################
    def set_html(self, html_content):
        """
        Establece el contenido HTML del video de YouTube.

        Args:
            html_content (str): Contenido HTML a establecer.
        """
        self.html_content = html_content
        if self.DEBUG:
            logger.info(f"Contenido HTML establecido con éxito para el video {self.video_id}.")
        
    def fetch_html_content(self, url_type='id', ovr_id=None, scrap_url=None):
        """ 
        Obtiene el contenido HTML del video de YouTube dado.

        Args:
            url_type (str): Tipo de URL a utilizar ('id' o 'url').
            ovr_id (str): ID del video a usar en lugar del atributo actual.
            scrap_url (str): URL personalizada para hacer scraping.
        """
        # Si se proporciona un ID de video para sobrescribir, úsalo
        if ovr_id is not None:
            logger.warning(f"Se va a cambiar el ID del video {self.video_id} por {ovr_id}")
            self.video_id = ovr_id
            
        # Define una URL por defecto para hacer scraping
        if scrap_url is None:
            scrap_url = 'https://www.youtube.com/watch?v='

        # Construye la URL del video de YouTube según el tipo
        if url_type == 'id':
            scrap_url = f'https://www.youtube.com/watch?v={self.video_id}'
        elif url_type == 'url':
            scrap_url = scrap_url
            # Expresión regular para extraer el valor del parámetro 'v'
            match = re.search(r'[?&]v=([^&]+)', scrap_url)
            if match:
                self.video_id = match.group(1)
        else:
            logger.error("Tipo de URL no válido o scrap_url no proporcionado para 'url'.")
            return

        # Obtiene el contenido HTML
        self.html_content = get_http_response(scrap_url, response_type='text')
        
        if self.html_content is None:
            logger.error(f"No se pudo obtener el contenido HTML para el video {self.video_id}.")

    def save_html_content(self, html_content=None):
        """
        Guarda el contenido HTML del video en un archivo.

        Args:
            html_content (str, optional): Contenido HTML a guardar. Si no se proporciona, se utiliza el contenido HTML del objeto.
        """
        try:
            # Si no se proporciona html_content, usa el contenido HTML del objeto
            if html_content is None:
                html_content = self.html_content
            
            # Genera el nombre del archivo con el ID del video y la fecha actual
            video_id = self.video_id
            current_date = get_formatted_date()
            filename = f'html_video_{video_id}_{current_date}.html'
            
            # Directorio donde se guardarán los archivos HTML
            filepath = os.path.join(os.environ.get("SOFT_RESULTS", ''), 'videos')
            
            # Crea el directorio si no existe
            os.makedirs(filepath, exist_ok=True)
            
            # Ruta completa del archivo
            filepath = os.path.join(filepath, filename)

            # Guarda el contenido HTML en el archivo
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(html_content)
            
            logger.info(f"Contenido HTML para el video {video_id} guardado correctamente en: {filepath}")
        
        except Exception as e:
            logger.error(f"No se pudo guardar el contenido HTML para el video {video_id}. Error: {e}")

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

            # Si hubo un fallo al obtener el código HTML del video, logeo un error y salgo de la función
            if self.html_content in [False, None]:
                logger.error(f"No se dispone de contenido HTML para el video {self.video_id}.")
                return False

            if self.SAVE_HTML:
                self.save_html_content()

            # Crear el diccionario para los datos
            video_data = {
                'video_id': self.video_id,  # Tiene que estar siempre este campo
                'channel_id': self._fetch_channel_id(),
                'channel_name': self._fetch_channel_name(),
                'title': self._fetch_video_title(),
                'views': self._fetch_video_views(),
                'mvm': self._fetch_most_viewed_moment(),
                'publish_date': self._fetch_publish_date(),
                'likes': self._fetch_video_likes(),
                'length': self._fetch_video_length(),
                'tags': self._fetch_video_tags(),
                'comment_count': self._fetch_video_comments_count()
            }

            # Actualiza la información del video con los datos obtenidos del scraping
            self.load_from_dict(video_data)
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
    
    def _fetch_channel_id(self, pattern=None):
        """Obtiene el ID del canal de Youtube para el video a partir del contenido HTML.

        Args:
            pattern (str, opcional): Patrón de búsqueda para extraer el ID del canal del video.

        Returns:
            str: ID del canal de Youtube.

        Notas:
            - Este método tiene un algoritmo principal y uno alternativo.
        """
        try:
            # Si no se proporciona un patrón, se utiliza uno predeterminado
            pattern = r'"channelId":"(.*?)"' if pattern is None else pattern

            # Intenta obtener el ID del canal del video utilizando el patrón dado en el HTML
            channel_id = self._fetch_data_from_pattern(pattern, self.html_content)

            # Si se encuentra el ID del canal del video, devolverlo
            if channel_id:
                return channel_id

        except Exception as e:
            # Registra un mensaje de error si no se puede obtener el ID del canal del video
            logger.error(f"No se pudo obtener el ID del canal para el video {self.video_id}: {str(e)}")

        # Establece un valor predeterminado de None si no se puede obtener el ID del canal del video
        return self.DEFAULT_VALUES['channel_id']

    def _fetch_channel_name(self, pattern=None):
        """Obtiene el nombre del canal de Youtube para el video a partir del contenido HTML.

        Args:
            pattern (str, opcional): Patrón de búsqueda para extraer el nombre del canal del video.

        Returns:
            str: Nombre del canal de Youtube.

        Notas:
            - Este método tiene un algoritmo principal y uno alternativo.
        """
        try:
            # Si no se proporciona un patrón, se utiliza uno predeterminado
            pattern = r'"ownerChannelName":"(.*?)"' if pattern is None else pattern

            # Intenta obtener el nombre del canal del video utilizando el patrón dado en el HTML
            channel_name = self._fetch_data_from_pattern(pattern, self.html_content)

            # Si se encuentra el nombre del canal del video, devolverlo
            if channel_name:
                return channel_name

        except Exception as e:
            # Registra un mensaje de error si no se puede obtener el nombre del canal del video
            logger.error(f"No se pudo obtener el nombre del canal para el video {self.video_id}: {str(e)}")

        # Establece un valor predeterminado de None si no se puede obtener el nombre del canal del video
        return self.DEFAULT_VALUES['channel_name']

    def _fetch_video_title(self, pattern=None):
        """ 
        Obtiene el título del video utilizando un patrón sobre el contenido HTML cargado.
        Registra un error si no se puede obtener el título del video.

        Args:
            pattern (opcional): Patrón de búsqueda para extraer el título del video.

        Notas:
            - Este método tiene un algoritmo principal y uno alternativo.
            - El título del video se establece como 'Unknown' si todo falla.
        """
        try:
            # Si se proporciona un patrón personalizado, úsalo, si no, usa uno predeterminado
            pattern = r'"title":"(.*?)"' if pattern is None else pattern

            # Obtener la información requerida utilizando el método clásico
            title = self._fetch_data_from_pattern(pattern, self.html_content)

            # Si se obtiene el título, devolverlo
            if title:
                return title

            # Construir una URL alternativa para hacer scraping si el método principal falla
            url = f'https://www.youtube.com/oembed?url=http://www.youtube.com/watch?v={self.video_id}&format=json'
            # Obtener la respuesta HTTP
            response = requests.get(url)
            # Transformar a datos JSON
            data = json.loads(response.text)
            # Obtener el título del video
            title = data['title']

            return title

        except re.error as e:
            logger.error(f"Fallo al aplicar el patrón de búsqueda {pattern} para el video {self.video_id}.")
        except AttributeError as e:
            logger.error(f"Error de atributo {e} al obtener los datos para el patron {pattern} para el video {self.video_id}.")
        except Exception as e:
            logger.error(f"Error inesperado al obtener el título para el video {self.video_id}: {str(e)}")

        # Establecer un título predeterminado si todo lo anterior falla
        return self.DEFAULT_VALUES['title']

    def _fetch_video_views(self, pattern=None):
        """ 
        Obtiene la cantidad de vistas del video utilizando un patrón sobre el contenido HTML cargado.
        Registra un error si no se puede obtener la cantidad de vistas del video.

        Args:
            pattern (opcional): Patrón de búsqueda para extraer la cantidad de vistas del video.

        Notas:
            - Este método tiene un algoritmo principal y uno alternativo.
            - Las vistas del video se establecen en 0 si todo falla.
        """
        try:
            # Si se proporciona un patrón personalizado, úsalo, si no, usa uno predeterminado
            pattern = r'"viewCount":"(.*?)"' if pattern is None else pattern

            # Intentar obtener los datos utilizando el patrón dado
            views = self._fetch_data_from_pattern(pattern, self.html_content)

            # Si se obtienen las vistas, devolverlas
            if views:
                return int(views)

            # Intentar con un método alternativo si falla el método principal
            url = f'https://www.youtube.com/watch?v={self.video_id}'
            # Obtener la cantidad de reproducciones
            video = YouTube(url)
            return int(video.views)

        except re.error as e:
            logger.error(f"Fallo al aplicar el patrón de búsqueda {e} para el video {self.video_id}.")
        except Exception as e:
            logger.error(f"No se pudo obtener la cantidad de vistas para el video {self.video_id}: {str(e)}")

        # Establecer un valor predeterminado si todo lo anterior falla
        return self.DEFAULT_VALUES['views']

    def _fetch_most_viewed_moment(self, pattern=None):
        """ 
        Obtiene el momento más visto (MVM) del video utilizando un patrón sobre el contenido HTML cargado.
        Registra un error si no se puede obtener el momento más visto del video.

        Args:
            pattern (opcional): Patrón de búsqueda para extraer el momento más visto del video.

        Notas:
            - El MVM del video se establece en '00:00:00' si todo falla.
        """
        try:
            # Si se proporciona un patrón personalizado, úsalo, si no, usa uno predeterminado
            pattern = r'"decorationTimeMillis":(.*?),' if pattern is None else pattern

            # Intentar obtener el dato solicitado a partir de un patrón
            milliseconds = self._fetch_data_from_pattern(pattern, self.html_content)

            # Si se obtienen los milisegundos, calcular el tiempo en formato 'HH:MM:SS'
            if milliseconds:
                len_seconds = float(milliseconds) / 1000.0
                return get_time_len(len_seconds)

        except re.error as e:
            logger.error(f"Fallo al aplicar el patrón de búsqueda {e} para el video {self.video_id}.")
        except Exception as e:
            logger.error(f"No se pudo obtener el momento más visto para el video {self.video_id}: {str(e)}")

        # Establecer un valor predeterminado si todo lo anterior falla
        return self.DEFAULT_VALUES['mvm']

    def _fetch_publish_date(self, pattern_1=None, pattern_2=None):
        """ 
        Obtiene la fecha de publicación del video utilizando un patrón sobre el contenido HTML cargado.
        Registra un error si no se puede obtener la fecha de publicación del video.

        Args:
            pattern_1 (opcional): Patrón de búsqueda 1 para extraer la fecha de publicación del video.
            pattern_2 (opcional): Patrón de búsqueda 2 para extraer la fecha de publicación del video.

        Notas:
            - Este método tiene un algoritmo principal y uno alternativo.
            - La fecha de publicación del video se establece en '00/00/00' si todo falla.
        """
        try:
            # Si se proporciona un patrón personalizado, úsalo, si no, usa uno predeterminado
            pattern_1 = r'"uploadDate":"(.*?)"' if pattern_1 is None else pattern_1
            pattern_2 = r'"publishDate":"(.*?)"' if pattern_2 is None else pattern_2

            # Intentar obtener la fecha de publicación utilizando el primer patrón
            publish_date = self._fetch_data_from_pattern(pattern_1, self.html_content)
            
            # Si obtengo un resultado valido termino la ejecucion
            if publish_date:
                # Convertir la cadena a un objeto datetime
                fecha_objeto = datetime.fromisoformat(publish_date)
                # Formatear la fecha en el nuevo formato
                publish_date = fecha_objeto.strftime("%Y-%m-%d %H:%M:%S")
                return publish_date

            # Intentar obtener la fecha de publicación utilizando el segundo patrón si falla el primero
            publish_date = self._fetch_data_from_pattern(pattern_2, self.html_content)
            
            # Si obtengo un resultado valido termino la ejecucion
            if publish_date:
                # Convertir la cadena a un objeto datetime
                fecha_objeto = datetime.fromisoformat(publish_date)
                # Formatear la fecha en el nuevo formato
                publish_date = fecha_objeto.strftime("%Y-%m-%d %H:%M:%S")
                return publish_date
            
        # Gestion de errores
        except ValueError as e:
            logger.error(f"Fallo al intentar formatear la fecha de publicación para el video {self.video_id}. Error: {e}")
        except re.error as e:
            logger.error(f"Fallo al aplicar los patrones de búsqueda {pattern_1}, {pattern_2} para obtener la fecha de publicacion para el video {self.video_id}.")
        except Exception as e:
            logger.error(f"No se pudo obtener la fecha de publicación para el video {self.id}: {str(e)}")

        return self.DEFAULT_VALUES['publish_date']

    def _fetch_video_likes(self, pattern=None):
        """ 
        Obtiene la cantidad de likes del video utilizando un patrón sobre el contenido HTML cargado.
        Registra un error si no se puede obtener la cantidad de likes del video.

        Args:
            pattern (opcional): Patrón de búsqueda para extraer la cantidad de likes del video.

        Notas:
            - Este método tiene un algoritmo principal y uno alternativo.
            - La cantidad de likes del video se establece en 0 si todo falla.
        """
        # Establezco los patrones de busqueda
        # Si se proporciona un patrón personalizado, úsalo, si no, usa uno predeterminado
        patterns = []
        if pattern is not None:
            patterns.append( pattern )
        patterns.append( r'"likeCount":"(.*?)"' )
        patterns.append( r'"expandedLikeCountIfLiked":\{"content":"(.*?)"\}' )
        patterns.append( r'"expandedLikeCountIfDisliked":\{"content":"(.*?)"\}' )
        patterns.append( r'"expandedLikeCountIfIndifferent":\{"content":"(.*?)"\}' )
        
        try:
            for pattern in patterns:
                # Intentar obtener la cantidad de likes utilizando el patrón dado
                likes = self._fetch_data_from_pattern(pattern, self.html_content)
            
                # Si obtengo un resultado válido, conviértelo a entero
                if likes:
                    return clean_and_parse_number(likes)

            # Método alternativo
            # FIXME: EN PRUEBA
            # Transformar la respuesta a un objeto BS
            response = BeautifulSoup(self.html_content, 'html.parser')
            # Encontrar elementos <script>
            script_tags = response.find_all('script')
            # Encontrar el script que contiene "likeCount"
            for script_tag in script_tags:
                # Transformar a string
                script_text = script_tag.string
                # Verificar si el script contiene "likeCount"
                if script_text and '"likeCount":' in script_text:
                    try:
                        # Obtener la cantidad de likes del script
                        likes = int(re.search(pattern, script_text).group(1))
                        return likes
                    except Exception as e:
                        likes = None

        except AttributeError:
            # Si no se encuentra ningún script, registra un mensaje de error
            logger.error(f"No se encontraron scripts incrustados para obtener likes en el video {self.video_id}")
        except (ValueError, TypeError):
            # Si ocurre un error al convertir a entero, registra un mensaje de error
            logger.error(f"No se pudo convertir la cantidad de likes a entero para el video {self.video_id}")
        except Exception as e:
            # Registra un mensaje de error genérico para cualquier otro error
            logger.error(f"Error al obtener la cantidad de likes para el video {self.video_id}: {str(e)}")

        # Establecer un valor predeterminado si todo lo anterior falla
        return self.DEFAULT_VALUES['likes']

    def _fetch_video_length(self, pattern=None):
        """ 
        Obtiene la duración del video utilizando un patrón sobre el contenido HTML cargado.
        Registra un error si no se puede obtener la duración del video.

        Args:
            pattern (str, opcional): Patrón de búsqueda para extraer la duración del video.

        Returns:
            str: Duración del video en formato HH:MM:SS.

        Notas:
            - La duración del video se establece en '00:00:00' si todo falla.
        """
        try:
            # Si no se proporciona un patrón, utiliza uno predeterminado
            pattern = r'"lengthSeconds":"(.*?)",' if pattern is None else pattern

            # Intenta obtener la duración del video utilizando el patrón dado en el HTML
            len_seconds = self._fetch_data_from_pattern(pattern, self.html_content)

            # Si se encuentra la duración del video, conviértelo a formato HH:MM:SS y devuélvelo
            if len_seconds:
                return get_time_len(int(len_seconds))

        except Exception as e:
            # Registra un mensaje de error si no se puede obtener la duración del video
            logger.error(f"Error al obtener la duración del video {self.video_id}: {str(e)}")

        # Establece un valor predeterminado de '00:00:00' si no se puede obtener la duración del video
        return self.DEFAULT_VALUES['length']

    def _fetch_video_tags(self, pattern=None):
        """ 
        Obtiene las etiquetas del video utilizando un patrón sobre el contenido HTML cargado.
        Registra un error si no se pueden obtener las etiquetas del video.

        Args:
            pattern (str, opcional): Patrón de búsqueda para extraer las etiquetas del video.

        Returns:
            str: Etiquetas del video separadas por comas.

        Notas:
            - Las etiquetas del video se establecen en "None" si todo falla.
        """
        try:
            # Si no se proporciona un patrón, utiliza uno predeterminado
            pattern = r'"keywords":[ ]*\[(.*?)\]' if pattern is None else pattern

            # Intenta obtener las etiquetas del video utilizando el patrón dado en el HTML
            tags = self._fetch_data_from_pattern(pattern, self.html_content)

            # Si se encuentran las etiquetas del video, realiza el formateo adecuado y devuélvelas
            if tags:
                tags = tags.replace(',', '/')
                tags = tags.replace('\\n', ' ')
                tags = tags.replace('"', '')
                return tags

            # Intenta un método alternativo si falla el principal
            # Transformar a un objeto BeautifulSoup
            soup = BeautifulSoup(self.html_content, 'html.parser')
            # Buscar el elemento "meta" con el atributo "name" igual a "keywords"
            meta_element = soup.find('meta', attrs={'name': 'keywords'})
            
            if meta_element:
                tags = meta_element['content']
                tags = tags.replace(',', '/')
                tags = tags.replace('\\n', ' ')
                tags = tags.replace('"', '')
                return tags

        except AttributeError as e:
            logger.error(f"Error al acceder a un atributo {str(e)} mientras se obtenian las etiquetas del video {self.video_id}.")
        except KeyError as e:
            logger.error(f"Error al acceder a una clave {str(e)} mientras se obtenian las etiquetas del video {self.video_id}.")
        except Exception as e:
            # Registra un mensaje de error si no se pueden obtener las etiquetas del video
            logger.error(f"Error al obtener las etiquetas del video {self.video_id}: {str(e)}")

        # Establece un valor predeterminado de "None" si no se pueden obtener las etiquetas del video
        return self.DEFAULT_VALUES['tags']

    def _fetch_video_comments_count(self, pattern=None):
        """ 
        Obtiene el recuento de comentarios del video utilizando un patrón sobre el contenido HTML cargado.
        Registra un error si no se pueden obtener los comentarios del video.

        Args:
            pattern (str, opcional): Patrón de búsqueda para extraer el recuento de comentarios del video.

        Returns:
            int: Recuento de comentarios del video.

        Notas:
            - El recuento de comentarios del video se establece en 0 si todo falla.
        """
        # Establezco los patrones de busqueda
        # Si se proporciona un patrón personalizado, úsalo, si no, usa uno predeterminado
        patterns = []
        if pattern is not None:
            patterns.append( pattern )
        patterns.append( r'"commentCount":[ ]*\{(.*?)\}' )
        
        try:
            for pattern in patterns:
                # Intentar obtener la cantidad de likes utilizando el patrón dado
                comments_str = self._fetch_data_from_pattern(pattern, self.html_content)
            
                # Si obtengo un resultado válido, conviértelo a entero
                if comments_str:
                    matches = re.search(r'(\d+\.\d+)\s*([A-Za-z]*)', comments_str)
                    comments_cnt = matches.group(1)
                    scale = matches.group(2)
                    if scale:
                        comments_cnt += scale
                    
                    return clean_and_parse_number(comments_cnt)

        except re.error as e:
            # Registra un mensaje de error si falla la expresión regular
            logger.error(f"Fallo al aplicar el patrón de búsqueda {pattern} para obtener el recuento de comentarios del video {self.video_id}: {str(e)}")
        except Exception as e:
            # Registra un mensaje de error detallado si no se pueden obtener los comentarios del video
            logger.error(f"Error al obtener el recuento de comentarios del video {self.video_id}: {str(e)}")
        
        # Establece un valor predeterminado de 0 si no se pueden obtener los comentarios del video
        return self.DEFAULT_VALUES['comment_count']

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
                # Intento obtener los datos para el video
                video_data = youtube_api.fetch_video_data(self.video_id)

                # Si la última petición a la API fue exitosa, cargo los datos
                if youtube_api.last_request_success:
                    
                    # Actualizo la información del video
                    self.load_from_dict(video_data)
                    
                    if self.DEBUG:
                        logger.info("Los datos se cargaron exitosamente utilizando la API de YouTube.")
                    return True
                
                else:
                    if self.DEBUG:
                        logger.debug(f"Se intentó usar la API de YouTube para obtener los datos del video {self.video_id} pero hubo un fallo al procesar la petición.")
            else:
                if self.DEBUG:
                    logger.debug(f"Se intentó usar la API de YouTube para obtener los datos del video {self.video_id} pero la API está deshabilitada.")
        
        except Exception as e:
            logger.warning(f"Fallo al cargar datos utilizando la API de YouTube: {e}")

        return False

    ############################################################################
    # Actualizar los datos del video
    ############################################################################
    def fetch_data(self, info_dict=None, force_method=None):
        """
        Intenta cargar datos del video de YouTube utilizando diferentes métodos.

        El orden de preferencia para cargar los datos es el siguiente:
        1. Datos proporcionados durante la inicialización del objeto.
        2. Utilización de la API de YouTube.
        3. Scraping de contenido HTML.

        Si alguno de los métodos falla, se pasará automáticamente al siguiente método.

        Args:
            info_dict (dict): Diccionario con datos del video para cargar.
            force_method (str): Método para forzar la carga de datos ('api' para API de YouTube, 'html' para scraping HTML).

        Returns:
            bool: True si se cargaron los datos con éxito, False en caso contrario.
        """
        # Verifica si los datos ya están cargados
        if self.data_loaded:
            logger.info(f"Los datos del video {self.video_id} ya están cargados en el objeto YoutubeVideo.")
            self.fetch_status = True
            return

        # Intenta cargar datos del diccionario proporcionado durante la inicialización
        if info_dict:
            self.load_from_dict(info_dict)
            logger.info(f"Los datos del video {self.video_id} se cargaron exitosamente desde el diccionario proporcionado durante la inicialización.")
            self.fetch_status = True
            return

        # Verifica si se especificó un método forzado
        if force_method:
            logger.info(f"Los datos del video {self.video_id} se van a cargar forzadamente usando el método {force_method}.")
            
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
            
            logger.error(f"No se pudo cargar datos del video {self.video_id} de YouTube usando métodos forzados.")
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
        logger.error(f"No se pudo cargar datos del video {self.video_id} de YouTube.")
        self.fetch_status = False
        return
    
if __name__ == "__main__":
    # Crear una instancia de YoutubeVideo
    # video = YoutubeVideo(video_id='dQw4w9WgXcQ') # Rick Astley - Never Gonna Give You Up
    # video = YoutubeVideo(video_id='9bZkp7q19f0') # PSY - GANGNAM STYLE
    # video = YoutubeVideo(video_id='5a9ozuMcMYY') # One More Time - Jack Black
    video = YoutubeVideo(video_id='tVj0ZTS4WF4') # Maroon 5 - Sugar

    # Simular que los datos ya están cargados
    # Si está en True se acaba la ejecución del programa
    video.data_loaded = False

    # Llamar al método fetch_data
    success = video.fetch_data(force_method='html')

    # Verificar si se cargaron los datos con éxito
    if success:
        print("Los datos se cargaron con éxito.")
        print(str(video))
    else:
        print("Error al cargar los datos.")