# Imports estándar de Python
import os
# import sys

# Añade el directorio raíz del proyecto a sys.path
# current_path = os.path.dirname(os.path.abspath(__file__))
# project_root = os.path.abspath(os.path.join(current_path, '..', '..'))  # Ajusta según la estructura de tu proyecto
# sys.path.append(project_root)

# Imports de terceros
# Ninguno en este set

# Imports locales
from src.logger.logger import Logger
from src.utils.utils import getenv

################################################################################
# Genero una instancia del Logger
################################################################################
logger = Logger(os.path.basename(__file__)).get_logger()

class Product:
    ############################################################################
    # Métodos de inicialización
    ############################################################################
    # Valores por defecto para los atributos de la clase
    DEBUG = False
    DEFAULT_SAVE_HTML = False
    DEFAULT_VALUES = {
        'product_id': None,
        'product_name': '',
        'description': '',
        'price': 0.0,
        'installments': 1,
        'currency': 'USD',  # Moneda común por defecto, ajustable según el contexto
        'ranking': 0,
        'rating': 0.0,
        'rating_count': 0,
        'platform': 'General',  # Valor por defecto para plataforma
        'store': '-',
        'is_best_seller': 0,
        'is_promoted': 0,
        'topic': '',
        'url': None
    }

    def __init__(self, product_id=None, info_dict=None):
        # Inicialización de la clase con valores por defecto y datos opcionales
        self.set_default_values()

        # Si se proporciona un ID de producto, lo usamos
        if product_id is not None:
            self.product_id = product_id

        # Si se proporciona un diccionario de información, lo usamos
        if info_dict:
            self.load_from_dict(info_dict)
        
        # Defino si tengo que guardar los HTML
        self.save_html = getenv('PRODUCTS_SAVE_HTML', self.DEFAULT_SAVE_HTML)
        
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
        """Devuelve todos los campos de la clase para ser mostrados en pantalla o en un archivo."""
        info_str = (
            f"- ID del producto: {self.product_id}\n"
            f"- Nombre del producto: {self.product_name}\n"
            f"- Descripción del producto: {self.description}\n"
            f"- Precio del producto: {self.price}\n"
            f"- Cuotas: {self.installments}\n"
            f"- Moneda: {self.currency}\n"
            f"- Ranking: {self.ranking}\n"
            f"- Calificación: {self.rating}\n"
            f"- Cantidad de calificaciones: {self.rating_count}\n"
            f"- Plataforma: {self.platform}\n"
            f"- Tienda: {self.store}\n"
            f"- Más vendido: {self.is_best_seller}\n"
            f"- Promocionado: {self.is_promoted}\n"
            f"- Tematica: {self.topic}\n"
            f"- URL del producto: {self.url}\n"
        )
        return info_str

    ############################################################################
    # Funciones de obtención de código HTML
    ############################################################################
    def save_html_content(self, html_content=None):
        """
        Guarda el contenido HTML del producto en un archivo.

        Args:
            html_content (str, optional): Contenido HTML a guardar. Si no se proporciona, se utiliza el contenido HTML del objeto.
        """
        try:
            if html_content is None:
                html_content = self.html_content
            
            product_id = self.product_id
            current_date = self.get_formatted_date()
            filename = f'html_product_{product_id}_{current_date}.html'
            
            filepath = os.path.join(os.environ.get("SOFT_RESULTS", ''), 'products')
            os.makedirs(filepath, exist_ok=True)
            
            with open(os.path.join(filepath, filename), 'w', encoding='utf-8') as file:
                file.write(html_content)
            
            logger.info(f"Contenido HTML para el producto {product_id} guardado correctamente en: {filepath}")
        
        except Exception as e:
            logger.error(f"No se pudo guardar el contenido HTML para el producto {product_id}. Error: {e}")
    