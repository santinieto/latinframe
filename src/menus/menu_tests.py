from src.logger.logger import Logger
from src.youtube.youtube_api import YoutubeAPI
from src.utils.mail import *
import os

# Crear un logger
logger = Logger(os.path.basename(__file__)).get_logger()

def menu_tests(app):
    """
    Configura la pantalla del menú de Productos en la aplicación.

    Args:
        app: La instancia de la aplicación de la interfaz gráfica.
    """
    logger.info('Menu de gestion de pruebas.')
    try:
        app.screen()  # Limpia la pantalla
        app.add_option("Youtube API Health Check", lambda: test_youtube_api())
        app.add_option("Test mail", lambda: test_mail())
        app.add_option("Test Logger", lambda: test_logger())
        app.add_option("Volver", lambda: app.main_menu())
    except AttributeError as e:
        print(f"Error al configurar el menú de Productos: {e}")

def test_youtube_api():
    youtube_api = YoutubeAPI()
    youtube_api.health_check()
    logger.info(f'- API en funcionamiento: {youtube_api.enabled}')

def test_mail():
    send_mail()
    
def test_logger():
    logger.info(f'Mensaje de informacion')
    logger.debug(f'Mensaje de debug')
    logger.error(f'Mensaje de error')
    logger.warning(f'Mensaje de warning')
    logger.critical(f'Mensaje critico')