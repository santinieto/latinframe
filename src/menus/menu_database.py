# Imports estándar de Python
# import os
# import sys

# Añade el directorio raíz del proyecto a sys.path
# current_path = os.path.dirname(os.path.abspath(__file__))
# project_root = os.path.abspath(os.path.join(current_path, '..', '..'))  # Ajusta según la estructura de tu proyecto
# sys.path.append(project_root)

# Imports de terceros
# Ninguno en este set

# Imports locales
from src.database.db_fetch import *

def menu_database(app):
    """
    Configura la pantalla del menú de Base de datos en la aplicación.

    Args:
        app: La instancia de la aplicación de la interfaz gráfica.
    """
    logger.info('Menu de operaciones con la base de datos.')
    try:
        app.screen()  # Limpia la pantalla
        app.add_option("Ejecutar SQL", lambda: print("Ejecutar SQL"))
        app.add_option("Sanidad de canales de YouTube", lambda: youtube_db_fetch())
        app.add_option("Exportar BD a CSV", lambda: sql_export_db(sel='.csv'))
        app.add_option("Exportar BD a Excel", lambda: sql_export_db(sel='.xlsx'))
        app.add_option("Volver", lambda: app.main_menu())
    except AttributeError as e:
        print(f"Error al configurar el menú de Base de datos. Error: {e}")
        