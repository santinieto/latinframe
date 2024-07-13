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
from src.youtube.youtube_manager import YoutubeManager
from src.youtube.youtube_manager import initialize_youtube_channel
from src.youtube.youtube_manager import initialize_youtube_video
from src.youtube.youtube_manager import initialize_youtube_short
from src.youtube.youtube_manager import initialize_youtube_playlist
from src.youtube.youtube_manager import initialize_youtube_video_from_db
from src.logger.logger import Logger

################################################################################
# Genero una instancia del Logger
################################################################################
logger = Logger(os.path.basename(__file__)).get_logger()

def menu_youtube(app):
    """
    Configura la pantalla del menú de YouTube en la aplicación.

    Args:
        app: La instancia de la aplicación de la interfaz gráfica.
    """
    logger.info('Menu de operaciones con Youtube.')
    try:
        app.screen()  # Limpia la pantalla
        app.add_option("Actualizar todo", lambda: fetch_all_youtube_data())
        app.add_option("Canales", lambda: menu_channel(app))
        app.add_option("Playlists", lambda: menu_playlist(app))
        app.add_option("Videos", lambda: menu_video(app))
        app.add_option("Shorts", lambda: menu_short(app))
        app.add_option("Volver", lambda: app.main_menu())
    except AttributeError as e:
        print(f"Error al configurar el menú de YouTube. Error: {e}")
        
def fetch_all_youtube_data():
    """
    Actualiza todos los datos de YouTube.
    """
    try:
        logger.info('Actualizando datos totales de YouTube...')
    
        # Creo el objeto unico que gestiona los productos
        youtube_manager = YoutubeManager(
                    load_channels_from_database=True,
                    load_videos_from_database=True,
                    channel_ids=[]
                )
        
        # Nota, en el caso del manager de YouTube, la carga en la base de datos
        # se hace adentro de la clase, no necesito un metodo get_data()
        youtube_manager.fetch_data(
            initialize_channels=True,
            initialize_videos=True,
            insert_data_to_db=True
        )
        
        youtube_manager.log_channels_info()
        youtube_manager.log_videos_info()
        
        logger.info('Proceso finalizado')
        
    except Exception as e:
        logger.error(f'Error al actualizar datos de YouTube. Error: {e}')
    
def menu_channel(app):
    """
    Configura la pantalla del menú de gestión de canales en la aplicación.
    """
    try:
            app.screen()  # Limpia la pantalla
            app.add_option("Buscar canal en internet", lambda: fetch_channel_data_from_internet(app))
            app.add_option("Buscar canal en la BD", lambda: print('Proximament disponible!'))
            app.add_option("Agregar canal a la BD", lambda: print('Proximament disponible!'))
            app.add_option("Borrar canal de la BD", lambda: print('Proximament disponible!'))
            app.add_option("Ver datos de canal", lambda: print('Proximament disponible!'))
            app.add_option("Volver", lambda: menu_youtube(app))
    except AttributeError as e:
        logger.error(f"Error al configurar el menú de gestión de canales. Error: {e}")

def menu_playlist(app):
    """
    Configura la pantalla del menú de gestión de canales en la aplicación.
    """
    try:
            app.screen()  # Limpia la pantalla
            app.add_option("Buscar playlist en internet", lambda: fetch_playlist_data_from_internet(app))
            app.add_option("Buscar playlist en la BD", lambda: print('Proximament disponible!'))
            app.add_option("Agregar playlist a la BD", lambda: print('Proximament disponible!'))
            app.add_option("Borrar playlist de la BD", lambda: print('Proximament disponible!'))
            app.add_option("Ver datos de playlist", lambda: print('Proximament disponible!'))
            app.add_option("Volver", lambda: menu_youtube(app))
    except AttributeError as e:
        logger.error(f"Error al configurar el menú de gestión de canales. Error: {e}")

def menu_video(app):
    """
    Configura la pantalla del menú de gestión de videos en la aplicación.
    """
    try:
        app.screen()  # Limpia la pantalla
        app.add_option("Buscar video en internet", lambda: fetch_video_data_from_internet(app))
        app.add_option("Buscar video en la BD", lambda: fetch_video_data_from_database(app))
        app.add_option("Agregar video a la BD", lambda: print('Proximament disponible!'))
        app.add_option("Borrar video de la BD", lambda: print('Proximament disponible!'))
        app.add_option("Ver datos de video", lambda: print('Proximament disponible!'))
        app.add_option("Volver", lambda: menu_youtube(app))
    except AttributeError as e:
        logger.error(f"Error al configurar el menú de gestión de videos. Error: {e}")

def menu_short(app):
    """
    Configura la pantalla del menú de gestión de videos en la aplicación.
    """
    try:
        app.screen()  # Limpia la pantalla
        app.add_option("Buscar short en internet", lambda: fetch_short_data_from_internet(app))
        app.add_option("Agregar short a la BD", lambda: print('Proximament disponible!'))
        app.add_option("Borrar short de la BD", lambda: print('Proximament disponible!'))
        app.add_option("Ver datos de short", lambda: print('Proximament disponible!'))
        app.add_option("Volver", lambda: menu_youtube(app))
    except AttributeError as e:
        logger.error(f"Error al configurar el menú de gestión de shorts. Error: {e}")
    
def fetch_channel_data_from_internet(app):
    """
    Obtiene datos de un canal de YouTube desde Internet.
    """
    try:
        partial_initialize_youtube_channel = partial(initialize_youtube_channel, verbose=True)
            
        app.screen()  # Limpia la pantalla
        app.add_label("Ingrese el ID o URL del canal:")
        app.add_user_input(
                placeholder="UC_x5XG1OV2P6uZZ5FSM9Ttw",
                submit_command=partial_initialize_youtube_channel,
                btn_text='Obtener datos'
            )
        app.add_option("Volver", lambda: menu_youtube(app))
    except Exception as e:
        logger.error(f'Error al obtener datos del canal desde Internet. Error: {e}')

def fetch_playlist_data_from_internet(app):
    """
    Obtiene datos de un canal de YouTube desde Internet.
    """
    try:
        partial_initialize_youtube_channel = partial(initialize_youtube_playlist, verbose=True)
            
        app.screen()  # Limpia la pantalla
        app.add_label("Ingrese el ID o URL de la playlist:")
        app.add_user_input(
                placeholder="PLBRoHO-L7e4Iw_JjEw2IlpE_FeR-wzgPS",
                submit_command=partial_initialize_youtube_channel,
                btn_text='Obtener datos'
            )
        app.add_option("Volver", lambda: menu_youtube(app))
    except Exception as e:
        logger.error(f'Error al obtener datos de la playlist desde Internet. Error: {e}')

def fetch_video_data_from_internet(app):
    """
    Obtiene datos de un video de YouTube desde Internet.
    """
    try:
        partial_initialize_youtube_video = partial(initialize_youtube_video, verbose=True)
        
        app.screen()  # Limpia la pantalla
        app.add_label("Ingrese el ID o URL del video:")
        app.add_user_input(
                placeholder="JGr6fTNTp7o",
                submit_command=partial_initialize_youtube_video,
                btn_text='Obtener datos'
            )
        app.add_option("Volver", lambda: menu_video(app))
    except Exception as e:
        logger.error(f'Error al obtener datos del video desde Internet: {e}')

def fetch_short_data_from_internet(app):
    """
    Obtiene datos de un short de YouTube desde Internet.
    """
    try:
        partial_initialize_youtube_short = partial(initialize_youtube_short, verbose=True)
        
        app.screen()  # Limpia la pantalla
        app.add_label("Ingrese el ID o URL del short:")
        app.add_user_input(
                placeholder="5Q18_KxEQTQ",
                submit_command=partial_initialize_youtube_short,
                btn_text='Obtener datos'
            )
        app.add_option("Volver", lambda: menu_short(app))
    except Exception as e:
        logger.error(f'Error al obtener datos del short desde Internet: {e}')
        
def fetch_video_data_from_database(app):
    """
    Obtiene datos de un video de YouTube desde la base de datos.
    """
    try:
        partial_initialize_youtube_video = partial(initialize_youtube_video_from_db, verbose=True)
        
        app.screen()  # Limpia la pantalla
        app.add_label("Ingrese el ID")
        app.add_user_input(
                placeholder="1M0ZTXaqP3Q",
                submit_command=partial_initialize_youtube_video,
                btn_text='Obtener datos'
            )
        app.add_option("Volver", lambda: menu_video(app))
    except Exception as e:
        logger.error(f'Error al obtener datos del video desde la base de datos: {e}')