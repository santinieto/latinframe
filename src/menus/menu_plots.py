# Imports estándar de Python
import os
# import sys

# Añade el directorio raíz del proyecto a sys.path
# current_path = os.path.dirname(os.path.abspath(__file__))
# project_root = os.path.abspath(os.path.join(current_path, '..', '..'))  # Ajusta según la estructura de tu proyecto
# sys.path.append(project_root)

# Imports de terceros
from functools import partial

# Imports locales
from src.logger.logger import Logger
from src.database.db_plots import *

################################################################################
# Genero una instancia del Logger
################################################################################
logger = Logger(os.path.basename(__file__)).get_logger()

def menu_plots(app):
    """
    Configura la pantalla del menú de Productos en la aplicación.

    Args:
        app: La instancia de la aplicación de la interfaz gráfica.
    """
    logger.info('Menu de dibujos.')
    try:
        app.screen()  # Limpia la pantalla
        app.add_option("Canales de Youtube", lambda: menu_youtube_channel_plots(app))
        app.add_option("Volver", lambda: app.main_menu())
    except AttributeError as e:
        print(f"Error al configurar el menú de Productos: {e}")

def menu_youtube_channel_plots(app):
    """
    Obtiene datos de un canal de YouTube desde Internet.
    """
    try:
        partial_channel_plots = partial(channel_plots, use_clean_data=True)
            
        app.screen()  # Limpia la pantalla
        app.add_label("Ingrese el ID del canal:")
        app.add_user_input(
                placeholder="UC36xmz34q02JYaZYKrMwXng",
                submit_command=partial_channel_plots,
                btn_text='Obtener gráficos'
            )
        app.add_option("Volver", lambda: menu_plots(app))
    except Exception as e:
        logger.error(f'Error al obtener datos del canal desde Internet. Error: {e}')

def channel_plots(channel_id_sel='', use_clean_data=True):
    """
    Genera gráficos a partir de los datos de canal almacenados en archivos CSV.
    
    Parameters:
    - use_clean_data (bool): Si es True, utiliza los archivos CSV limpios. Si no se encuentran,
        utiliza los archivos normales. Si es False, utiliza los archivos normales.
    
    Excepciones:
    - KeyError: Si las variables de entorno necesarias no están definidas.
    - FileNotFoundError: Si los archivos CSV no se encuentran.
    - pd.errors.EmptyDataError: Si los archivos CSV están vacíos.
    - pd.errors.ParserError: Si los archivos CSV contienen errores de formato.
    - Exception: Para cualquier otro error inesperado.
    """
    try:
        # Defino los nombres de los archivos
        base_path = os.path.join(os.environ['SOFT_RESULTS'], 'db')
        filename_1 = os.path.join(base_path, 'channel_records.csv')
        filename_2 = os.path.join(base_path, 'channel.csv')

        if use_clean_data:
            clean_filename_1 = filename_1.replace('.csv', '_clean.csv')
            clean_filename_2 = filename_2.replace('.csv', '_clean.csv')

            try:
                # Intenta cargar los archivos limpios
                df_1 = pd.read_csv(clean_filename_1)
                df_2 = pd.read_csv(clean_filename_2)
            except FileNotFoundError:
                logger.warning("Archivos limpios no encontrados, intentando con archivos normales.")
                # Si falla, intenta con los archivos normales
                df_1 = pd.read_csv(filename_1)
                df_2 = pd.read_csv(filename_2)
        else:
            # Si no se usa clean data, intenta cargar los archivos normales
            df_1 = pd.read_csv(filename_1)
            df_2 = pd.read_csv(filename_2)

        # Hago los plots de las tablas de canal
        plot_channel_tables(channel_id_sel, df_1, df_2)

    except KeyError as e:
        logger.error(f"Variable de entorno no definida: {e}")
    except FileNotFoundError as e:
        logger.error(f"Archivo no encontrado para el canal [{channel_id_sel}]. Error: {e}")
    except pd.errors.EmptyDataError as e:
        logger.error(f"Archivo CSV vacío para el canal [{channel_id_sel}]. Error: {e}")
    except pd.errors.ParserError as e:
        logger.error(f"Error al parsear el archivo CSV para el canal [{channel_id_sel}]. Error: {e}")
    except Exception as e:
        logger.error(f"Ocurrió un error inesperado al realizar los graficos para el canal [{channel_id_sel}]. Error: {e}")