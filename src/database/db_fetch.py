import os
import pandas as pd
import datetime
import shutil

from src.database.db import Database
from src.database.db_clean import *
from src.utils.utils import get_formatted_date
from src.utils.utils import get_dir_files
from src.utils.utils import get_newest_file
from src.utils.logger import Logger

# Crear un logger
logger = Logger().get_logger()

def youtube_db_fetch():
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Obtengo el directorio actual
    home = os.getcwd()

    # Seteo variables de entorno
    os.environ["SOFT_UTILS"] = os.path.join(home, 'utils')

    # Obtengo la lista de canales que esta en el .csv
    utils_path = os.environ.get("SOFT_UTILS")
    csv_path = os.path.join(utils_path, "Youtube_channelIDs.csv")
    channels_df = pd.read_csv(csv_path).dropna().dropna(axis=1)
    csv_ids = channels_df['channelID'].to_list()

    # Abro la conexion con la base datos
    with Database() as db:
        # Obtengo todos los IDs presentes en la base de datos
        db_channel_ids = db.get_youtube_channel_ids(table_name = 'CHANNEL')
        db_channel_records_ids = db.get_youtube_channel_ids(table_name = 'CHANNEL_RECORDS')
        db_video_ids = db.get_youtube_channel_ids(table_name = 'VIDEO')

        # Combino todas las listas y me quedo con los que no esten en la tabla CHANNEL
        total_id_list = list(set(csv_ids + db_channel_ids + db_channel_records_ids + db_video_ids))
        to_add_list = [x for x in total_id_list if x not in db_channel_ids]

        # Agrego los canales faltantes
        for to_add_id in to_add_list:
            query = '''
            INSERT OR REPLACE INTO CHANNEL (
                CHANNEL_ID, CHANNEL_NAME, UPDATE_DATE
            ) VALUES (?, ?, ?)
            '''
            params = (
                to_add_id,
                '<channel_name>',
                current_time
            )
            db.exec(query, params)
            logger.info(f'Se agrego el canal [{to_add_id}] a la tabla DB.[CHANNEL]')

def sql_restore_db_backup():
    backups_dir = 'db_backups/'
    db_backups = get_dir_files(path=backups_dir)
    target_backup = get_newest_file(db_backups)

    with Database() as db:
        shutil.copy(backups_dir + target_backup, db.db_name)

    logger.info(f'Se restauró una base de datos [{backups_dir + target_backup}]')
    
def sql_generate_db_backup():
    """
    Genero un backup de la base de datos anexandole la fecha
    y hora actual
    """

    date = get_formatted_date()

    # Abro la conexion con la base de datos
    with Database() as db:

        # Rutas de origen y destino
        backup_dir = 'db_backups'
        bkp_filename = os.path.join(backup_dir, db.db_name.replace('.db', f'_{date}.db'))

        try:
            # Crea el directorio si no existe
            os.makedirs(backup_dir, exist_ok=True)
            
            # Copia el archivo de la ruta de origen a la ruta de destino
            shutil.copy(db.db_name, bkp_filename)
            logger.info(f"Archivo copiado de [{db.db_name}] a [{bkp_filename}].")
        except FileNotFoundError:
            logger.error("El archivo de origen no fue encontrado.")
        except shutil.SameFileError:
            logger.error("El archivo de origen y destino son el mismo archivo.")
        except PermissionError:
            logger.error("No tienes permisos para copiar el archivo.")
        except Exception as e:
            logger.error(f"Ocurrió un error inesperado. Error: [{e}]")

def sql_clean_db_pre_export():
    with Database() as db:
        
        # Busco los canales que tienen registros pero no estan
        # en la tabla de canales
        query = '''
        select distinct channel_id
        from channel_records
        where channel_id not in (
            select distinct channel_id from channel
        )
        '''
        results = db.select(query, ())
        results_list = [x[0] for x in results]
        logger.info( f'Lista de canales sin registros en CHANNEL: {results_list}' )
        
        for channel_id in results_list:
            
            logger.info(f'Borrando canal {channel_id} de la tabla CHANNEL')
            query = f'delete from channel where channel_id = "{channel_id}"'
            db.exec(query, ())
            
            logger.info(f'Borrando canal {channel_id} de la tabla CHANNEL_RECORDS')
            query = f'delete from channel_records where channel_id = "{channel_id}"'
            db.exec(query, ())
        
        # Busco los canales que estan en la tabla de videos
        # y que no estan en la tabla de canales
        query = '''
        select distinct channel_id
        from channel
        where channel_id not in (
            select distinct channel_id from video
        )
        '''
        results = db.select(query, ())
        results_list = [x[0] for x in results]
        logger.info( f'Lista canales con videos sin registros en CHANNEL: {results_list}' )
        
        for channel_id in results_list:
            
            logger.info(f'Borrando canal {channel_id} de la tabla CHANNEL')
            query = f'delete from channel where channel_id = "{channel_id}"'
            db.exec(query, ())
            
            logger.info(f'Borrando canal {channel_id} de la tabla CHANNEL_RECORDS')
            query = f'delete from channel_records where channel_id = "{channel_id}"'
            db.exec(query, ())

        # Busco los videos que tienen registros pero no estan
        # en la tabla de videos
        query = '''
        select distinct video_id
        from video_records
        where video_id not in (
            select distinct video_id from video
        )
        '''
        results = db.select(query, ())
        results_list = [x[0] for x in results]
        logger.info( f'Lista de videos sin registros en VIDEO: {results_list}' )
        
        for video_id in results_list:
            
            logger.info(f'Borrando video {video_id} de la tabla VIDEO')
            query = f'delete from video where video_id = "{video_id}"'
            db.exec(query, ())
            
            logger.info(f'Borrando video {video_id} de la tabla VIDEO_RECORDS')
            query = f'delete from video_records where video_id = "{video_id}"'
            db.exec(query, ())

def sql_export_db(sel='.csv'):
    """
    Exporta la base de datos a un archivo con la extensión especificada.
    
    Parameters:
    - sel (str): La extensión del archivo a exportar. Puede ser '.csv' o '.xlsx'. Por defecto es '.csv'.
    
    Excepciones:
    - ValueError: Si se proporciona una extensión no soportada.
    - Exception: Para cualquier otro error inesperado durante el proceso de exportación.
    """
    # Validación de la extensión seleccionada
    if sel not in ['.csv', '.xlsx']:
        raise ValueError("Extensión no soportada. Use '.csv' o '.xlsx'.")
    
    try:
        sql_clean_db_pre_export()
        
        with Database() as db:
            db.export_table(ext=sel)
        
        sql_clean_db_post_export()
        
    except ValueError as ve:
        logger.error(f"Valor no válido: {ve}")
        raise
    except Exception as e:
        logger.error(f"Ocurrió un error inesperado durante la exportación de la base de datos: {e}")
        raise

def sql_clean_db_post_export():
    # Defino los nombres de los archivo
    FILENAME_1 = os.environ['SOFT_RESULTS'] + '/db/' + r'channel_records.csv'
    FILENAME_2 = os.environ['SOFT_RESULTS'] + '/db/' + r'channel.csv'
    FILENAME_3 = os.environ['SOFT_RESULTS'] + '/db/' + r'video_records.csv'
    FILENAME_4 = os.environ['SOFT_RESULTS'] + '/db/' + r'video.csv'
    FILENAME_5 = os.environ['SOFT_RESULTS'] + '/db/' + r'similarweb_records.csv'
    FILENAME_6 = os.environ['SOFT_RESULTS'] + '/db/' + r'similarweb_domains.csv'

    # Obtengo los CSV limpios de tablas de canales
    logger.info('Limpiando tablas de canales de Youtube...')
    df_1, df_2 = clean_channel_tables(
        filename_1 = FILENAME_1,
        filename_2 = FILENAME_2
    )

    # Obtengo los CSV limpios de videos de canales
    logger.info('Limpiando tablas de videos de Youtube...')
    df_3, df_4 = clean_video_tables(
        filename_1 = FILENAME_3,
        filename_2 = FILENAME_4
    )

    # Obtengo los CSV limpios de videos de canales
    logger.info('Limpiando tablas de SimilarWeb...')
    df_5, df_6 = clean_similarweb_tables(
        filename_1 = FILENAME_5,
        filename_2 = FILENAME_6
    )