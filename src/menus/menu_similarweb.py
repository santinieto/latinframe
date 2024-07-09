from src.similarweb.similarweb_manager import SimilarWebManager
from src.logger.logger import Logger
from functools import partial
import os

# Crear un logger
logger = Logger(os.path.basename(__file__)).get_logger()

def menu_similarweb(app):
    """
    Configura la pantalla del menú de SimilarWeb en la aplicación.

    Args:
        app: La instancia de la aplicación de la interfaz gráfica.
    """
    logger.info('Menu de operaciones con SimilarWebs.')
    try:
        app.screen()  # Limpia la pantalla
        app.add_option("Actualizar todo", lambda: fetch_similarwebs_data())
        app.add_option("Buscar dominio", lambda: fetch_similarweb_domain(app))
        app.add_option("Agregar dominio", lambda: add_similarweb_domain(app))
        app.add_option("Volver", lambda: app.main_menu())
    except AttributeError as e:
        logger.error(f"Error al configurar el menú de SimilarWeb: {e}")

def fetch_similarwebs_data():
    # Creo el objeto
    similarweb_manager = SimilarWebManager()
    
    # Prueba general
    # Nota, en el caso del manager de SimilarWeb, la carga en la base de datos
    # se hace adentro de la clase, no necesito un metodo get_webs()
    similarweb_manager.fetch_data()
    
def fetch_similarweb_domain(app):
    """
    """
    # Creo el objeto
    similarweb_manager = SimilarWebManager()
    
    try:
        partial_get_web = partial(similarweb_manager.get_web)
        
        app.screen()  # Limpia la pantalla
        app.add_label("Ingrese el dominio a buscar:")
        app.add_user_input(
                placeholder="youtube.com",
                submit_command=partial_get_web,
                btn_text='Obtener datos'
            )
        app.add_option("Volver", lambda: menu_similarweb(app))
    except Exception as e:
        logger.error(f'Error al obtener datos del video desde Internet: {e}')

def add_similarweb_domain(app):
    """
    """
    # Creo el objeto
    similarweb_manager = SimilarWebManager()
    
    try:
        partial_add_web = partial(similarweb_manager.add_web)
        
        app.screen()  # Limpia la pantalla
        app.add_label("Ingrese el dominio a agregar:")
        app.add_user_input(
                placeholder="youtube.com",
                submit_command=partial_add_web,
                btn_text='Agregar'
            )
        app.add_option("Volver", lambda: menu_similarweb(app))
    except Exception as e:
        logger.error(f'Error al obtener datos del video desde Internet: {e}')