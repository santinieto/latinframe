from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
from urllib.parse import urlparse, urlunparse
from pathlib import Path
import threading

from src.utils.logger import Logger
from src.utils.environment import set_environment

################################################################################
# Crear un logger
################################################################################
logger = Logger().get_logger()

################################################################################
# Clase principal
################################################################################
class Driver:
    ############################################################################
    # Metodos de incializacion
    ############################################################################
    # Valores por defecto para los atributos de la clase
    DRIVERS_PATH = r'drivers/'
    RESULTS_PATH = r'results/similarweb/'
    DEFAULT_BROWSER = 'chrome'
    DEFAULT_WAIT_TIME = 8
    
    def __init__(self, max_concurrent=4): # FIXME: NO ESTOY USANDO BROWSER
        """
        Inicializa el objeto Driver con el navegador especificado (por defecto, Chrome).

        Args:
            browser (str): El navegador a utilizar: 'chrome', 'firefox', o 'edge'.
            drivers_path (str): Ruta al directorio donde se encuentran los controladores del navegador.
            results_path (str): Ruta al directorio donde se guardarán los resultados.
        """

        # Atributos
        self.max_concurrent = max_concurrent
        self.drivers_path = self.DRIVERS_PATH
        self.results_path = self.RESULTS_PATH
        self.html_contents = {}
        self.drivers = {}  # Diccionario para manejar múltiples instancias del driver
    
    def __del__(self):
        """
        Destructor para cerrar el navegador cuando se libera la instancia de la clase.
        """
        self.cleanup()

    def __enter__(self):
        """
        Context manager para usar Driver con 'with'.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Manejo de limpieza al salir del contexto 'with'.
        """
        self.cleanup()

    def close_driver(self, driver_key='0'):
        """
        Cierra el navegador y libera los recursos asociados.
        """
        if driver_key in self.drivers:
            self.drivers[driver_key].quit()
            del self.drivers[driver_key]

    def cleanup(self):
        """
        Realiza la limpieza necesaria al finalizar el uso del objeto Driver.
        """
        for driver_key in list(self.drivers.keys()):
            self.close_driver(driver_key)

    def set_driver(self, browser=None):
        """
        Abre el navegador especificado en el atributo self.browser.
        """
        # Me fijo si uso un navegador en particular
        if not browser:
            browser = self.DEFAULT_BROWSER
        
        # Obtengo los controladores del navegador
        browser_options = self._get_browser_options(browser)

        try:
            # Configuración del navegador
            service = browser_options["service"](os.path.join(self.drivers_path, browser_options["driver_name"]))
            options = browser_options["options"]()

            for arg in browser_options["args"]:
                options.add_argument(arg)
            
            for key, value in browser_options["experimental_options"].items():
                options.add_experimental_option(key, value)

            # Inicialización del WebDriver
            return webdriver.__dict__[browser.capitalize()](service=service, options=options)

        except Exception as e:
            logger.error(f"Error al abrir el navegador. Error: {e}")

    def _get_browser_options(self, browser):
        """
        Retorna las opciones específicas para el navegador dado.

        Args:
            browser (str): El navegador a utilizar: 'chrome', 'firefox', o 'edge'.

        Returns:
            dict: Un diccionario con las opciones específicas del navegador.
        """
        browser_options = {
            "chrome": {
                "driver_name": "chromedriver.exe",
                "service": ChromeService,
                "options": ChromeOptions,
                "args": ["--disable-usb-device-detection"],
                "experimental_options": {'excludeSwitches': ['enable-logging']}
            },
            "firefox": {
                "driver_name": "geckodriver.exe",
                "service": FirefoxService,
                "options": FirefoxOptions,
                "args": [],
                "experimental_options": {}
            },
            "edge": {
                "driver_name": "msedgedriver.exe",
                "service": EdgeService,
                "options": EdgeOptions,
                "args": [],
                "experimental_options": {}
            }
        }

        if browser not in browser_options:
            raise ValueError(f"Navegador no válido. Debe ser 'chrome', 'firefox' o 'edge'. Navegador recibido: [{browser}]")

        return browser_options[browser]
    
    ############################################################################
    # Gestión del contenido HTML
    ############################################################################
    def _update_html_content(self, driver_key='0'):
        """
        Actualiza el contenido HTMl en el objeto.
        """
        try:
            if driver_key in self.drivers:
                self.html_contents[driver_key] = self.drivers[driver_key].page_source
        except Exception as e:
            logger.error(f'Error al actualizar el contenido HTML para el driver {driver_key}. Error: {e}')

    def save_html_to_file(self, driver_key='0', filename="scraped_page.html"):
        """
        Guarda el contenido HTML en el archivo deseado.
        """
        try:
            # Me aseguro que el path es valido
            filename = self._sanitize_filename(filename)
            
            # Verificar y crear el directorio si es necesario
            file_path = Path(filename)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Guardo el contenido HTML
            with file_path.open("w", encoding="utf-8") as file:
                file.write(self.html_contents.get(driver_key, ''))
            logger.info(f'Se guardó el contenido HTML en el archivo [{filename}]')
        except Exception as e:
            logger.error(f"Error al intentar guardar contenido HTML en el archivo [{filename}]. Error: {e}")
    
    ############################################################################
    # Metodos de uso
    ############################################################################
    def open_url(self, driver_key='0', url='http://www.google.com/', wait_time=None, element_selector=None, browser=None):
        """
        Carga una página web y guarda el HTML en un archivo.

        Args:
            driver_key (str): Clave para identificar la instancia del driver.
            url (str): La URL de la página web a cargar.
            wait_time (int, optional): Tiempo en segundos que se espera antes de cerrar el navegador.
            element_selector (str, optional): Selector del elemento HTML que se espera antes de cerrar el navegador.
        """
        # Valores por defecto
        browser = browser or self.DEFAULT_BROWSER
        wait_time = wait_time or self.DEFAULT_WAIT_TIME
        
        if driver_key not in self.drivers:
            self.drivers[driver_key] = self.set_driver(browser)
        
        if not self.drivers[driver_key]:
            logger.error(f"El driver [{driver_key}] no está inicializado. No se puede obtener la URL [{url}].")
            return
        
        try:
            # Normalizo la URL
            url = self._normalize_url(url)
            
            # Mensaje de debug
            logger.info(f'Se va a abrir la URL [{url}] en el driver [{driver_key}]')
            
            # Abro la URL y actualizo su contenido HTML
            self.drivers[driver_key].get(url)
            
            # Establezco las condiciones
            if element_selector:
                WebDriverWait(self.drivers[driver_key], wait_time).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, element_selector))
                )
            elif wait_time:
                time.sleep(wait_time)
            
            # Actualizo y guardo el contenido HTML
            self._update_html_content(driver_key)
            filename = self.generate_filename(url)
            self.save_html_to_file(driver_key, filename=filename)
            
            # Cierro el driver actual
            self.close_driver(driver_key)
        except TimeoutException as te:
            logger.error(f"Elemento HTML [{element_selector}] no encontrado en la URL [{url}] luego de [{wait_time}] segundos.")
        except ValueError as ve:
            logger.error(f"URL inválida [{url}]. Error: {ve}")
        except Exception as e:
            logger.error(f"Error desconocido al cargar la URL [{url}]. Error: {e}.")

    def open_multiple_urls(self, urls, wait_time=None, element_selector=None, browser=None):
        """
        Abre múltiples URLs en diferentes hilos.

        Args:
            urls (list): Lista de URLs a cargar.
            wait_time (int, optional): Tiempo en segundos que se espera antes de cerrar el navegador.
            element_selector (str, optional): Selector del elemento HTML que se espera antes de cerrar el navegador.
        """
        semaphore = threading.Semaphore(self.max_concurrent)
        threads = []
        
        # Valores por defecto
        browser = browser or self.DEFAULT_BROWSER
        wait_time = wait_time or self.DEFAULT_WAIT_TIME
        
        # Me aseguro que sea una lista porque sino voy a recorrer letra por letra
        # de la cadena
        if not isinstance(urls, list):
            urls = [urls]

        # Abro cada URL
        for i, url in enumerate(urls):
            args = (url, semaphore, wait_time, element_selector, browser)
            thread = threading.Thread(target=self._open_url_with_semaphore, args=args)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    def _open_url_with_semaphore(self, url, semaphore, wait_time=None, element_selector=None, browser='chrome'):
        """
        Función interna para abrir una URL con un semáforo para controlar el número máximo de páginas abiertas simultáneamente.

        Args:
            driver_key (str): Clave para identificar la instancia del driver.
            url (str): La URL de la página web a cargar.
            semaphore (threading.Semaphore): Semáforo para controlar el acceso concurrente.
            wait_time (int, optional): Tiempo en segundos que se espera antes de cerrar el navegador.
            element_selector (str, optional): Selector del elemento HTML que se espera antes de cerrar el navegador.
        """
        with semaphore:
            driver_key = f"driver_{threading.get_ident()}"
            self.open_url(driver_key, url, wait_time, element_selector, browser)
            self.close_driver(driver_key)

    def open_url_and_wait(self, url, driver_key='0', timeout=10, browser=None):
        """
        Abre una página web y espera hasta que se cumpla una condición antes de guardar el HTML.

        Args:
            url (str): La URL de la página web a cargar.
            driver_key (str): Clave para identificar la instancia del driver.
            condition (función de espera): La condición a esperar antes de guardar el HTML.
                Puede ser una función que espere hasta que se cumpla cierta condición (por ejemplo, presencia de un elemento).
            timeout (int): Tiempo máximo en segundos para esperar a que se cumpla la condición.

        Returns:
            bool: True si la condición se cumplió y se guardó el HTML correctamente, False en caso contrario.
        """
        # Valores por defecto
        browser = browser or self.DEFAULT_BROWSER
        wait_time = wait_time or self.DEFAULT_WAIT_TIME
        
        if driver_key not in self.drivers:
            self.drivers[driver_key] = self.set_driver(browser)
            
        try:
            # Normalizo la URL
            url = self._normalize_url(url)
            
            # Mensaje de debug
            logger.info(f'Se va a abrir la URL [{url}] en el driver [{driver_key}]')
            
            # Abro la URL y actualizo su contenido HTML
            self.drivers[driver_key].get(url)
            
            # Espero la cantidad de tiempo que el usuario pide
            time.sleep(timeout)
            
            # Actualizar y guardo el contenido HTML
            self._update_html_content(driver_key)
            filename = self.generate_filename(url)
            self.save_html_to_file(driver_key, filename=filename)
        except TimeoutException:
            logger.error(f"Tiempo de espera agotado ({timeout} segundos) para la condición en la URL: {url}")
            return False
        except WebDriverException as e:
            logger.error(f"Error al cargar la URL '{url}' con WebDriver: {e}")
            return False
        except Exception as e:
            logger.error(f"Error desconocido al cargar la URL '{url}': {e}")
            return False

    ############################################################################
    # Utilidades
    ############################################################################
    def _normalize_url(self, url):
        """
        Normaliza la URL, añadiendo 'https://' si no tiene un esquema válido.

        Args:
            url (str): La URL a normalizar.

        Returns:
            str: La URL normalizada.
        """
        parsed_url = urlparse(url)
        
        if not parsed_url.scheme:
            # Si no tiene esquema, añadir 'https://'
            normalized_url = urlunparse(('https', parsed_url.netloc, parsed_url.path,
                                            parsed_url.params, parsed_url.query, parsed_url.fragment))
            logger.info(f"URL normalizada: '{url}' => '{normalized_url}'")
            return normalized_url
        elif parsed_url.scheme not in ['http', 'https']:
            # Si tiene un esquema inválido, lanzar un error o adaptar según sea necesario
            raise ValueError(f"Esquema de URL inválido: {parsed_url.scheme}. Debe ser 'http' o 'https'.")
        
        return url
    
    def _sanitize_filename(self, filename):
        """
        Sanitiza el nombre del archivo para asegurarse de que no contiene caracteres no válidos.

        Args:
            filename (str): El nombre del archivo a sanitizar.

        Returns:
            str: El nombre del archivo sanitizado.
        """
        return "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_', '/')).rstrip()

    def generate_filename(self, url):
        """
        Genera un alias para el nombre de archivo basado en la URL.

        Args:
            url (str): URL para la cual se generará el alias.

        Returns:
            str: Alias generado para el nombre de archivo.
        """
        # Remueve protocolo y formatea la URL
        url = url.replace("://", "_")
        url = url.replace("/", "_")
        url = url.replace("#", "_")
        url = url.replace("-", "_")
        cleaned_url = url.replace(".", "_")

        # Elimina los duplicados de guiones bajos
        cleaned_url = '_'.join(cleaned_url.split('_')).strip('_')
        
        # Creo el nombre del archivo
        filename = f'html_{cleaned_url}.dat'
        filepath = os.path.join(self.results_path, filename)

        return filepath

################################################################################
# Funciones de checkeo para el driver (FIXME: CODIGO QUE NO ESTOY USANDO)
################################################################################
def element_present_by_structure(driver, struct="//div[@id='target']/span"):
    """
    Verifica si un elemento específico está visible en la página mediante XPath.

    Args:
        driver (WebDriver): Instancia del WebDriver de Selenium.

    Returns:
        bool: True si el elemento está visible, False si no.
    """
    try:
        element = driver.find_element(By.XPATH, struct)
        return element.is_displayed()
    except NoSuchElementException:
        return False

def url_changed(driver, url="https://example.com/loading"):
    """
    Verifica si la URL actual ha cambiado desde una URL de carga específica.

    Args:
        driver (WebDriver): Instancia del WebDriver de Selenium.

    Returns:
        bool: True si la URL ha cambiado, False si no.
    """
    current_url = driver.current_url
    return current_url != url

def ajax_complete(driver):
    """
    Verifica si no hay peticiones AJAX activas en la página.

    Args:
        driver (WebDriver): Instancia del WebDriver de Selenium.

    Returns:
        bool: True si no hay peticiones AJAX activas, False si hay peticiones activas.
    """
    return driver.execute_script("return jQuery.active == 0")

################################################################################
# Test principal del programa
################################################################################
if __name__ == "__main__":
    set_environment()
    
    # Creo el objeto de tipo driver
    driver_manager = Driver()
    urls = [
            "https://www.google.com",
            "https://www.youtube.com",
            "https://www.facebook.com",
            "https://www.similarweb.com/website/google.com/#overview",
            "https://www.similarweb.com/website/youtube.com/#overview"
        ]
    driver_manager.open_multiple_urls(urls, element_selector='.app-section__content')
    
    # # Armo una lista de webs a visitar
    # url_list =[
    #     ('https://www.similarweb.com/website/youtube.com/', 'youtube'),
    #     ('https://www.similarweb.com/website/google.com/', 'google'),
    # ]

    # # Otros ejemplos
    # # driver.open_url("https://www.ejemplo.com")
    # # driver.open_url("https://www.similarweb.com/top-websites/")

    # # Obtengo el codigo HTML para esas paginas
    # driver.scrap_url_list(url_list, 20)

    # Cierro la pagina
    # driver.close_driver()
