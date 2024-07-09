import os

from src.logger.logger import Logger
from src.utils.utils import getenv
import os

# Crear un logger
logger = Logger(os.path.basename(__file__)).get_logger()

class New:
    ############################################################################
    # Métodos de inicialización
    ############################################################################
    # Valores por defecto para los atributos de la clase
    DEBUG = False
    DEFAULT_SAVE_HTML = False
    DEFAULT_VALUES = {
        'new_id': None,                 # Identificador de la noticia
        'title': '',                    # Título de la noticia
        'topic': '',                    # Temática de la noticia
        'topic_id': None,               # Identificador de la temática
        'newspaper': 1,                 # Identificador del periódico por defecto
        'newspaper_id': None,           # Identificador del periódico
        'publish_date': '00/00/00',     # Fecha de publicación
        'antique': 0.0,                 # Antigüedad de la noticia
        'url': None                     # URL de la noticia
    }

    def __init__(self, new_id=None, info_dict=None):
        # Inicialización de la clase con valores por defecto y datos opcionales
        self.set_default_values()
        self.save_html = getenv('NEWS_SAVE_HTML', self.DEFAULT_SAVE_HTML)

        # Si se proporciona un ID de la noticia, lo usamos
        if new_id is not None:
            self.new_id = new_id

        # Si se proporciona un diccionario de información, lo usamos
        if info_dict:
            self.load_from_dict(info_dict)
        
        # Este no va en el diccionario
        self.html_content = None

    def set_default_values(self):
        """Establece los valores por defecto."""
        for key, value in self.DEFAULT_VALUES.items():
            setattr(self, key, value)

    def load_from_dict(self, info_dict):
        """Carga los valores desde un diccionario si se proporciona."""
        for key, value in info_dict.items():
            if key in self.DEFAULT_VALUES:
                setattr(self, key, value)

    def to_dicc(self):
        """Convierte el objeto a un diccionario con los valores actuales."""
        return {key: getattr(self, key) for key in self.DEFAULT_VALUES}
    
    def __str__(self):
        """
        Devuelve todos los campos de la clase para ser mostrados en pantalla o en un archivo.

        Returns:
            str: Cadena con los valores de los atributos de la clase.
        """
        info_str = (
            f"- ID de la noticia: {self.new_id}\n"
            f"- Título: {self.title}\n"
            f"- Temática: {self.topic}\n"
            f"- ID de la temática: {self.topic_id}\n"
            f"- Periódico: {self.newspaper}\n"
            f"- ID del periódico: {self.newspaper_id}\n"
            f"- Fecha de publicación: {self.publish_date}\n"
            f"- Antigüedad: {self.antique}\n"
            f"- URL: {self.url}"
        )
        return info_str

    ############################################################################
    # Funciones de obtención de código HTML
    ############################################################################
    def save_html_content(self, html_content=None):
        """
        Guarda el contenido HTML de la noticia en un archivo.

        Args:
            html_content (str, optional): Contenido HTML a guardar. Si no se proporciona, se utiliza el contenido HTML del objeto.
        """
        try:
            if html_content is None:
                html_content = self.html_content
            
            new_id = self.new_id
            current_date = self.get_formatted_date()
            filename = f'html_new_{new_id}_{current_date}.html'
            
            filepath = os.path.join(os.environ.get("SOFT_RESULTS", ''), 'news')
            os.makedirs(filepath, exist_ok=True)
            
            with open(os.path.join(filepath, filename), 'w', encoding='utf-8') as file:
                file.write(html_content)
            
            logger.info(f"Contenido HTML para la noticia [{new_id}] guardado correctamente en: {filepath}")
        
        except Exception as e:
            logger.error(f"No se pudo guardar el contenido HTML para la noticia {new_id}. Error: {e}")
    