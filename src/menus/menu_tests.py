from src.logger.logger import Logger
from src.youtube.youtube_api import YoutubeAPI
from src.utils.mail import *
from src.utils.driver import Driver
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
        app.add_option("Send Mail", lambda: test_mail())
        app.add_option("Test Logger", lambda: test_logger())
        app.add_option("SimilarWeb Open URL", lambda: test_open_url())
        app.add_option("SimilarWeb Open Multiple URLs", lambda: test_open_mult_urls())
        app.add_option("SimilarWeb MultiThreading (NO ANDA)", lambda: test_multithreading())
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
    
def test_open_url():
    """
    """
    # Creo el objeto
    driver = Driver()
    driver.open_url(url='www.youtube.com')
    
def test_open_mult_urls():
    driver_manager = Driver()
    urls = [
            "https://www.google.com",
            "https://www.youtube.com",
            "https://www.facebook.com",
            "https://www.similarweb.com/website/google.com/#overview",
            "https://www.similarweb.com/website/youtube.com/#overview"
        ]
    driver_manager.open_multiple_urls(urls, element_selector='.app-section__content')
    
def test_multithreading():
    import concurrent.futures

    driver_manager = Driver()
    urls = [
            "https://www.google.com",
            "https://www.youtube.com",
            "https://www.facebook.com",
            "https://www.similarweb.com/website/google.com/#overview",
            "https://www.similarweb.com/website/youtube.com/#overview"
        ]
    
    def open_url_task(url):
        driver_manager.open_url(url)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(open_url_task, url) for url in urls]
        concurrent.futures.wait(futures)