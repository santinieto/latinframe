import os
import re
import json
import requests
from pytube import YouTube
from datetime import datetime
from bs4 import BeautifulSoup

from src.logger.logger import Logger
from src.utils.utils import get_formatted_date
from src.utils.utils import get_similarweb_url_tuple
from src.utils.utils import getenv

# Crear un logger
logger = Logger(os.path.basename(__file__)).get_logger()

class SimilarWebTopWebsitesTable:
    ############################################################################
    # Metodos de inicializacion
    ############################################################################
    # Valores por defecto para los atributos de la clase
    
    DEFAULT_SAVE_HTML = True
    BASE_URL = 'https://www.similarweb.com/'
    DEFAULT_FILENAME = 'html_top_websites.dat'
    
    def __init__(self, filename=None):
        self.filename = filename or self.DEFAULT_FILENAME
        self.row_data = []
        self.save_html = getenv('SIMILARWEB_SAVE_HTML', self.DEFAULT_SAVE_HTML)
        self.html_content = ''
        self.data_loaded = False
        self.fetch_status = False
        
        if self.filename is not None:
            self.set_html_content_fromfile(filename=self.filename)
    
    ############################################################################
    # Funciones de obtención de contenido HTML
    ############################################################################
    def set_html_content(self, html_content):
        """Establece el contenido HTML de la tabla."""
        self.html_content = html_content

    def set_html_content_fromfile(self, filename=None):
        """Carga el contenido HTML desde un archivo."""
        if filename is not None:
            self.filename = filename
        try:
            with open(self.filename, 'r', encoding="utf-8") as file:
                self.html_content = BeautifulSoup(file, 'html.parser')
            self.data_loaded = True
        except Exception as e:
            msg = f'No se pudo cargar el archivo {filename}: {str(e)}'
            logger.error(msg)
            self.data_loaded = False

    def save_html_content(self, html_content=None):
        """
        Guarda el contenido HTML de la tabla en un archivo.

        Args:
            html_content (str, optional): Contenido HTML a guardar. Si no se proporciona, se utiliza el contenido HTML del objeto.
        """
        try:
            # Si no se proporciona html_content, usa el contenido HTML del objeto
            if html_content is None:
                html_content = self.html_content

            # Genera el nombre del archivo con una marca de tiempo actual
            current_date = get_formatted_date()
            filename = f'html_top_websites_{current_date}.html'
            
            # Directorio donde se guardarán los archivos HTML
            filepath = os.path.join(os.environ.get("SOFT_RESULTS", ''), 'websites')
            
            # Crea el directorio si no existe
            os.makedirs(filepath, exist_ok=True)
            
            # Ruta completa del archivo
            filepath = os.path.join(filepath, filename)

            # Guarda el contenido HTML en el archivo
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(str(html_content))
            
            logger.info(f"Contenido HTML de los sitios top guardado correctamente en: {filepath}")
        
        except Exception as e:
            logger.error(f"No se pudo guardar el contenido HTML. Error: {e}")
        
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
            # Si no tengo contenido HTML no puedo obtener informacion
            if self.html_content in [False, None]:
                logger.error(f"No se dispone de contenido HTML para el sitio para la tabla de SimilarWeb.")
                return False

            # Si se necesita guardar el HTML
            if self.save_html:
                self.save_html_content()

            # Obtengo los datos
            self.fetch_rows()
            
            logger.info("Los datos se cargaron exitosamente mediante scraping de contenido HTML.")
            return True

        except Exception as e:
            logger.warning(f"Fallo al cargar datos mediante scraping de contenido HTML: {e}")

        return False

    def fetch_rows(self):
        """Encuentra y extrae las filas de datos de la tabla HTML."""
        try:
            rows = self.html_content.find_all('tr', class_='top-table__row')
            
            if not rows:
                msg = 'No se pudieron obtener las filas para la tabla proporcionada'
                logger.error(msg)
                return

            self.row_data = []

            for row in rows:
                try:
                    row_dicc = {
                        'rank': row.find('span', class_='tw-table__rank').text.strip(),
                        'domain': row.find('span', class_='tw-table__domain').text.strip(),
                        'category': row.find(['span','a'], class_='tw-table__category').text.strip(),
                        'avg_visit_duration': row.find('span', class_='tw-table__avg-visit-duration').text.strip(),
                        'pages_per_visit': row.find('span', class_='tw-table__pages-per-visit').text.strip(),
                        'bounce_rate': row.find('span', class_='tw-table__bounce-rate').text.strip(),
                    }
                except Exception as e:
                    row_dicc = {
                        'rank': '',
                        'domain': '',
                        'category': '',
                        'avg_visit_duration': '',
                        'pages_per_visit': '',
                        'bounce_rate': '',
                    }
                    msg = f'No se pudieron recoger los campos para el diccionario. Código HTML:\n\n{row}\n\nError: {str(e)}'
                    logger.error(msg)
                self.row_data.append(row_dicc)
            
            self.data_loaded = True
            logger.info('Filas de datos extraídas correctamente.')

        except Exception as e:
            msg = f'Error al intentar obtener las filas de la tabla: {str(e)}'
            logger.error(msg)

    def get_url_list(self):
        """Genera una lista de URLs a partir de los datos de la fila."""
        try:
            self.url_list = []
            for data in self.row_data:
                url, alias = get_similarweb_url_tuple(data['domain'])
                self.url_list.append((url, alias))
            logger.info('Lista de URLs generada correctamente.')
            return self.url_list

        except Exception as e:
            msg = f'Error al generar la lista de URLs: {str(e)}'
            logger.error(msg)
            return []

class SimilarWebWebsite:
    ############################################################################
    # Metodos de inicializacion
    ############################################################################
    # Valores por defecto para los atributos de la clase
    BASE_URL = 'https://www.similarweb.com/website/'
    DEBUG = True
    DEFAULT_SAVE_HTML = False
    DEFAULT_VALUES = {
        'domain_id': '',
        'domain': '',
        'global_rank': 0,
        'country_rank': 0,
        'category_rank': 0,
        'total_visits': 0,
        'bounce_rate': 0.0,
        'pages_per_visit': 0.0,
        'avg_duration_visit': '00:00:00',
        'company': '',
        'year_founder': 0,
        'employees': '',
        'hq': '',
        'annual_revenue': '',
        'industry': '',
        'top_countries': []
    }

    def __init__(self, filename=None, info_dict=None):
        # Inicialización de la clase
        self.set_default_values()
        self.data_loaded = False
        self.html_content = None
        self.save_html = getenv('SIMILARWEB_SAVE_HTML', self.DEFAULT_SAVE_HTML)
        self.fetch_status = False
        self.filename = filename
        
        # Si hay un diccionario para cargar datos, lo usamos
        if info_dict:
            # Cargamos los valores desde un diccionario si se proporciona
            self.load_from_dict(info_dict)
        
        # Si se proporciona un archivo HTML, lo uso
        if self.filename is not None:
            self.set_html_content_fromfile(filename=filename)

    def set_default_values(self):
        """Establece los valores por defecto de los atributos de la clase."""
        for key, value in self.DEFAULT_VALUES.items():
            setattr(self, key, value)

    def load_from_dict(self, info_dict):
        """
        Carga los valores de un diccionario en los atributos de la clase.

        Args:
            info_dict (dict): Diccionario con los valores a cargar.
        """
        if 'domain' not in info_dict:
            # Registra un mensaje de error y sale si no se proporciona el campo 'domain'
            logger.error("El campo 'domain' no está presente en el diccionario de entrada.")
            return
        
        for key, value in info_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                logger.warning(f"No se encontró el campo [{key}] para asignar el valor del atributo de SimilarWebWebsite")
        
        self.data_loaded = True

    def to_dict(self):
        """
        Convierte los atributos de la clase en un diccionario.

        Returns:
            dict: Diccionario con los valores de los atributos de la clase.
        """
        return {attr: getattr(self, attr) for attr in self.DEFAULT_VALUES.keys()}

    def __str__(self):
        """Devuelve todos los campos de la clase para ser mostrados en pantalla o en un archivo."""
        info_str = (
            f"- ID de Dominio del sitio: {self.domain_id}\n"
            f"- Dominio del sitio: {self.domain}\n"
            f"- Compañía: {self.company}\n"
            f"- Año de fundación: {self.year_founder}\n"
            f"- Empleados de la compañía: {self.employees}\n"
            f"- Sede: {self.hq}\n"
            f"- Ingresos anuales: {self.annual_revenue}\n"
            f"- Industria: {self.industry}\n"
            f"- Ranking global: {self.global_rank}\n"
            f"- Ranking en el país: {self.country_rank}\n"
            f"- Ranking en la categoría: {self.category_rank}\n"
            f"- Visitas totales: {self.total_visits}\n"
            f"- Tasa de rebote del sitio: {self.bounce_rate}\n"
            f"- Páginas por visita: {self.pages_per_visit}\n"
            f"- Duración promedio de la visita: {self.avg_duration_visit}\n"
            f"- Países con mayor presencia: {self.top_countries}"
        )
        return info_str
    
    ############################################################################
    # Funciones de obtención de contenido HTML
    ############################################################################
    def set_html_content(self, html_content):
        """
        Establece el contenido HTML.

        Args:
            html_content (str): Contenido HTML a establecer.
        """
        self.html_content = html_content
        if self.DEBUG:
            logger.info(f"Contenido HTML establecido con éxito para el sitio {self.domain}.")

    def set_html_content_fromfile(self, filename=None):
        if filename is not None:
            self.filename = filename
        try:
            with open(self.filename, 'r', encoding="utf-8") as file:
                self.html_content = BeautifulSoup(file, 'html.parser')
        except Exception as e:
            msg = f'Could not save file {filename}: {e}'
            logger.error(msg)

    def save_html_content(self, html_content=None):
        """
        Guarda el contenido HTML del sitio en un archivo.

        Args:
            html_content (str, optional): Contenido HTML a guardar. Si no se proporciona, se utiliza el contenido HTML del objeto.
        """
        try:
            # Si no se proporciona html_content, usa el contenido HTML del objeto
            if html_content is None:
                html_content = self.html_content

            # Genera el nombre del archivo con el dominio y la fecha actual
            domain = self.domain
            current_date = get_formatted_date()
            filename = f'html_site_{domain}_{current_date}.html'
            
            # Directorio donde se guardarán los archivos HTML
            filepath = os.path.join(os.environ.get("SOFT_RESULTS", ''), 'sites')
            
            # Crea el directorio si no existe
            os.makedirs(filepath, exist_ok=True)
            
            # Ruta completa del archivo
            filepath = os.path.join(filepath, filename)

            # Guarda el contenido HTML en el archivo
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(str(html_content))
            
            logger.info(f"Contenido HTML para el sitio {domain} guardado correctamente en: {filepath}")
        
        except Exception as e:
            logger.error(f"No se pudo guardar el contenido HTML para el sitio {domain}. Error: {e}")

    ############################################################################
    # Obtencion de datos mediante el codigo HTML
    ############################################################################
    def fetch_data(self, info_dict=None):
        """
        Intenta cargar datos del sitio de SimilarWeb utilizando diferentes métodos.

        El orden de preferencia para cargar los datos es el siguiente:
        1. Datos proporcionados durante la inicialización del objeto.
        3. Scraping de contenido HTML.

        Si alguno de los métodos falla, se pasará automáticamente al siguiente método.

        Args:
            info_dict (dict): Diccionario con datos del video para cargar.
        """
        self.fetch_status = True
        
        # Verifica si los datos ya están cargados
        if self.data_loaded:
            logger.info(f"Los datos del sitio [{self.domain}] ya están cargados en el objeto SimilarWebWebsite.")
            return

        # Intenta cargar datos del diccionario proporcionado durante la inicialización
        if info_dict:
            self.load_from_dict(info_dict)
            logger.info(f"Los datos del sitio [{self.domain}] se cargaron exitosamente desde el diccionario proporcionado durante la inicialización.")
            self.data_loaded = True
            return
        
        # Intenta cargar datos mediante scraping de contenido HTML si no se especifica un método forzado
        if self._load_data_from_html():
            self.data_loaded = True
            return

        # Si no se pudo cargar datos de ninguna manera, registra un mensaje de error
        logger.error(f"No se pudieron cargar datos del sitio [{self.domain}] de SimilarWeb.")
        self.fetch_status = False
        return
    
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

            # Si hubo un fallo al obtener el código HTML del sitio, logeo un error y salgo de la función
            if self.html_content in [False, None]:
                logger.error(f"No se dispone de contenido HTML para el sitio {self.domain}.")
                return False

            # Si se necesita guardar el HTML
            if self.save_html:
                self.save_html_content()

            # Crear el diccionario para los datos
            site_data = {
                'domain': self._fetch_domain_from_html(),  # Tiene que estar siempre este campo
            }
            
            # Actualizar el diccionario de video_data con los valores adicionales
            site_data.update( self._fetch_info_from_html() )
            site_data.update( self._fetch_rank_from_html() )
            site_data.update( self._fetch_engagement_from_html() )
            
            # Obtengo el ranking de los paises donde mas se visita el sitio
            site_data['top_countries'] = self._fetch_top_countries()

            # Actualiza la información del sitio con los datos obtenidos del scraping
            self.load_from_dict(site_data)
            logger.info("Los datos se cargaron exitosamente mediante scraping de contenido HTML.")
            return True

        except Exception as e:
            logger.warning(f"Fallo al cargar datos mediante scraping de contenido HTML: {e}")

        return False
    
    def _fetch_domain_from_html(self):
        """
        Busca el dominio en el contenido HTML y lo asigna a self.domain.

        Returns:
            bool: True si se encontró y asignó el dominio correctamente, False en caso contrario.
        """
        domain = self.DEFAULT_VALUES['domain']
        
        try:
            # Busca el elemento <p> con la clase 'wa-overview__title' y obtiene su texto
            domain_element = self.html_content.find('p', class_='wa-overview__title')
            
            if domain_element:
                domain = domain_element.text.strip()
                return domain
            else:
                logger.warning("No se encontró el elemento del dominio en el contenido HTML.")
                return domain

        except AttributeError as e:
            logger.error(f"Error de atributo al buscar el domipnio: {e}")
            return domain
        except Exception as e:
            logger.error(f"Error inesperado al buscar el dominio: {e}")
            return domain
        
    def _fetch_info_from_html(self):
        """
        Busca y retorna valores adicionales en el contenido HTML como un diccionario.

        Returns:
            dict: Diccionario con los valores adicionales encontrados.
                Las claves son los nombres de los atributos y los valores son los datos correspondientes.
                Si no se pueden obtener los datos, las claves tendrán el valor None.
        """
        info = {
            'company': self.DEFAULT_VALUES['company'],
            'year_founder': self.DEFAULT_VALUES['year_founder'],
            'employees': self.DEFAULT_VALUES['employees'],
            'hq': self.DEFAULT_VALUES['hq'],
            'annual_revenue': self.DEFAULT_VALUES['annual_revenue'],
            'industry': self.DEFAULT_VALUES['industry']
        }

        try:
            info_box = self.html_content.find('div', class_= [
                'app-company-info',
                # 'wa-overview__company'
            ])
            if not info_box:
                logger.warning(f"No se encontró la caja de información para el dominio {self.domain}.")
                return info
            
            values = info_box.find_all('dd', 'app-company-info__list-item app-company-info__list-item--value')
            if len(values) < 6:
                logger.warning(f"Información incompleta para el dominio {self.domain}.")
                return info

            info['company'] = values[0].text.strip()
            info['year_founder'] = values[1].text.strip()
            info['employees'] = values[2].text.strip()
            info['hq'] = values[3].text.strip()
            info['annual_revenue'] = values[4].text.strip()
            info['industry'] = values[5].text.strip()

        except Exception as e:
            logger.error(f"No se pudieron obtener los valores adicionales para el dominio {self.domain}. Error: {e}")

        return info

    def _fetch_rank_from_html(self):
        """
        Intenta obtener y actualizar el ranking global, por país y por categoría desde el contenido HTML.
        """
        ranks = {
            'global_rank': self.DEFAULT_VALUES['global_rank'],
            'country_rank': self.DEFAULT_VALUES['country_rank'],
            'category_rank': self.DEFAULT_VALUES['category_rank']
        }
        
        try:
            # Obtengo el cuadro de encabezado
            rank_header = self.html_content.find('div', class_='wa-rank-list wa-rank-list--md')
            
            if rank_header:
                # Obtengo las cajas
                global_box = rank_header.find('div', class_='wa-rank-list__item wa-rank-list__item--global')
                country_box = rank_header.find('div', class_='wa-rank-list__item wa-rank-list__item--country')
                category_box = rank_header.find('div', class_='wa-rank-list__item wa-rank-list__item--category')
                
                # Obtengo los valores de las cajas si están presentes
                if global_box:
                    ranks['global_rank'] = int(global_box.find('p', class_='wa-rank-list__value').text.replace('#','').replace('.','').replace(',',''))
                if country_box:
                    ranks['country_rank'] = int(country_box.find('p', class_='wa-rank-list__value').text.replace('#','').replace('.','').replace(',',''))
                if category_box:
                    ranks['category_rank'] = int(category_box.find('p', class_='wa-rank-list__value').text.replace('#','').replace('.','').replace(',',''))
            
            else:
                logger.warning(f"No se encontró el encabezado de ranking para el dominio {self.domain}")
            
        except Exception as e:
            logger.error(f"No se pudo obtener la información de ranking para el dominio {self.domain}. Error: {e}")
        
        return ranks

    def _fetch_engagement_from_html(self):
        """
        Intenta obtener y actualizar la información de engagement desde el contenido HTML.
        """
        engagemenet = {
            'total_visits': self.DEFAULT_VALUES['total_visits'],
            'bounce_rate': self.DEFAULT_VALUES['bounce_rate'],
            'pages_per_visit': self.DEFAULT_VALUES['category_rank'],
            'avg_duration_visit': self.DEFAULT_VALUES['avg_duration_visit']
        }
        
        try:
            # Encuentro la caja de engagement
            engagement_box = self.html_content.find('div', class_='engagement-list')
            
            if engagement_box:
                # Encuentro los elementos dentro de la caja
                engagement_elements = engagement_box.find_all('div', class_='engagement-list__item')
                
                # Para cada elemento, obtengo el dato asociado si están presentes
                if len(engagement_elements) > 3:
                    bounce_rate_text = engagement_elements[1].find('p', class_='engagement-list__item-value').text.strip().replace('%','')
                    
                    engagemenet['total_visits'] = engagement_elements[0].find('p', class_='engagement-list__item-value').text.strip()
                    engagemenet['bounce_rate'] = round(float(bounce_rate_text) / 100.0, 2)
                    engagemenet['pages_per_visit'] = engagement_elements[2].find('p', class_='engagement-list__item-value').text.strip()
                    engagemenet['avg_duration_visit'] = engagement_elements[3].find('p', class_='engagement-list__item-value').text.strip()
            
            else:
                logger.warning(f"No se encontró la caja de engagement para el dominio {self.domain}")
        
        except Exception as e:
            logger.error(f"No se pudo obtener la información de engagement para el dominio {self.domain}. Error: {e}")

        return engagemenet

    def _fetch_top_countries(self):
        """
        Intenta obtener y actualizar la información sobre los países donde el sitio es más popular.
        
        Returns:
            list: Una lista de listas, donde cada sublista contiene el nombre del país,
                el tráfico del país y el cambio en el tráfico.
        """
        # Inicializo la lista
        # NOTA: Si no pongo el copy, entonces top_countries ocupa el mismo lugar
        #       en memoria que la lista por defecto y la piso.
        top_countries = self.DEFAULT_VALUES['top_countries'].copy()
        
        try:
            # Encuentra la caja de engagement
            top_countries_wrapper = self.html_content.find('div', class_='wa-geography__chart')
            if not top_countries_wrapper:
                logger.warning(f"No se encontró la caja contenedora sobre los países más populares para el sitio [{self.domain}]")
                return top_countries
            
            # Encuentra la tabla dentro de la caja de engagement
            top_countries_box = top_countries_wrapper.find('div', class_=[
                'wa-legend', 'wa-geography__legend'
            ])
            if not top_countries_box:
                logger.warning(f"No se encontró la tabla sobre los países más populares para el sitio [{self.domain}]")
                return top_countries
            
            # Encuentra todas las filas de países en la tabla
            rows = top_countries_box.find_all('div', class_='wa-geography__country')
            
            if rows:
                # Recorre cada fila de la tabla
                for row in rows:
                    # Obtiene el nombre del país, el tráfico y el cambio en el tráfico
                    country_name = row.find(['a','span'], class_='wa-geography__country-name').text
                    country_traffic = row.find('span', class_='wa-geography__country-traffic-value').text
                    
                    # Inicializa el cambio de tráfico
                    country_traffic_change = row.find('span', class_='wa-geography__country-traffic-change').text
                    if country_traffic_change:
                        country_traffic_change = country_traffic_change
                        # Verifica si el cambio porcentual es mayor que 0
                        if row.find('span', class_='app-parameter-change--up'):
                            country_traffic_change = '+' + country_traffic_change
                        elif row.find('span', class_='app-parameter-change--down'):
                            country_traffic_change = '-' + country_traffic_change
                        else:
                            logger.warning(f"No se encontró la dirección de cambio para el porcentaje de tráfico para el sitio [{self.domain}]")
                    else:
                        country_traffic_change = '0%'
                        
                    # Agrega los datos del país a la lista de top_countries
                    row_data = (country_name, country_traffic, country_traffic_change)
                    top_countries.append(row_data)
            else:
                logger.warning(f"No se encontraron países en la tabla de países más populares para el sitio [{self.domain}]")
            
        except Exception as e:
            logger.error(f"No se pudo obtener la información de países de mayor tráfico para el dominio [{self.domain}]. Error: {e}")

        return top_countries
    
if __name__ == '__main__':
    filename = 'results/similarweb/html_https_www_similarweb_com__website_ebay_com__overview.dat'
    
    # Obtengo la informacion a partir del contenido HTML
    web_info = SimilarWebWebsite(filename=filename)
    web_info.fetch_data()

    # Mostrar datos de la pagina
    logger.info(str(web_info))