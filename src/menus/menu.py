# Imports estándar de Python
# import os
# import sys

# Añade el directorio raíz del proyecto a sys.path
# current_path = os.path.dirname(os.path.abspath(__file__))
# project_root = os.path.abspath(os.path.join(current_path, '..', '..'))  # Ajusta según la estructura de tu proyecto
# sys.path.append(project_root)

# Imports de terceros
# Ninguna en este set

# Imports locales
from src.menus.menu_youtube import *
from src.menus.menu_similarweb import *
from src.menus.menu_news import *
from src.menus.menu_products import *
from src.menus.menu_database import *
from src.menus.menu_backups import *
from src.menus.menu_plots import *
from src.menus.menu_tests import *

def configure_main_menu(app):
    """
    Configura el menú principal de la aplicación agregando varias opciones.

    Args:
        app: La instancia de la aplicación de la interfaz gráfica.
    """
    try:
        app.add_main_menu_option("Ejecutar todo", lambda: run_all_processes())
        app.add_main_menu_option("YouTube", lambda: menu_youtube(app))
        app.add_main_menu_option("SimilarWeb", lambda: menu_similarweb(app))
        app.add_main_menu_option("Noticias", lambda: menu_news(app))
        app.add_main_menu_option("Productos", lambda: menu_products(app))
        app.add_main_menu_option("Base de datos", lambda: menu_database(app))
        app.add_main_menu_option("Resguardos", lambda: menu_backups(app))
        app.add_main_menu_option("Gráficos", lambda: menu_plots(app))
        app.add_main_menu_option("Tests", lambda: menu_tests(app))
        app.main_menu()
    except AttributeError as e:
        print(f"Error al configurar el menú principal: {e}")

def run_all_processes():
    logger.info('Se comienza la ejecucion general de la aplicacion.')
    fetch_all_news_data()
    fetch_products_data('all')
    fetch_all_youtube_data()
    fetch_similarwebs_data()