# Imports estándar de Python
import datetime
import os
import sqlite3
# import sys

# Añade el directorio raíz del proyecto a sys.path
# current_path = os.path.dirname(os.path.abspath(__file__))
# project_root = os.path.abspath(os.path.join(current_path, '..', '..'))  # Ajusta según la estructura de tu proyecto
# sys.path.append(project_root)

# Imports de terceros
import pandas as pd

# Imports locales
from src.logger.logger import Logger
from src.utils.utils import getenv, join_str

################################################################################
# Genero una instancia del Logger
################################################################################
logger = Logger(os.path.basename(__file__)).get_logger()

class Database:
    ############################################################################
    # Atributos globables
    ############################################################################
    DEFAULT_DB_NAME = 'latinframe.db'

    ############################################################################
    # Metodos de incializacion
    ############################################################################

    def __init__(self, db_name=None):
        # Nombre de la base de datos
        self.db_name = getenv('DB_NAME', self.DEFAULT_DB_NAME)
        self.conn = None
        self.cursor = None

        # Open connection
        self.db_open()

        # Create tables
        self.create_video_tables()
        self.create_short_tables()
        self.create_channel_tables()
        self.create_playlist_tables()
        self.create_similarweb_tables()
        self.create_news_tables()
        self.create_product_tables()

    ############################################################################
    # Métodos de gestión de la base de datos
    ############################################################################
    def __enter__(self):
        """ Método para permitir el uso de 'with' para manejar la conexión."""
        try:
            self.db_open()
            return self
        except sqlite3.Error as e:
            logger.error(f'Error al abrir la conexión con la base de datos: {str(e)}')

    def __exit__(self, exc_type, exc_value, traceback):
        """Método para cerrar la conexión al salir del bloque 'with'."""
        try:
            self.db_close()
        except sqlite3.Error as e:
            logger.error(f'Error al cerrar la conexión con la base de datos: {str(e)}')

    def db_open(self):
        """Método para abrir la conexión a la base de datos."""
        if self.conn is None:
            try:
                self.conn = sqlite3.connect(self.db_name)
                self.cursor = self.conn.cursor()
            except sqlite3.Error as e:
                logger.error(f'Error al abrir la conexión con la base de datos: {str(e)}')

    def db_close(self):
        """Método para cerrar la conexión a la base de datos """
        if self.conn is not None:
            try:
                self.conn.close()
                self.conn = None
                self.cursor = None
            except sqlite3.Error as e:
                logger.error(f'Error al cerrar la conexión con la base de datos: {str(e)}')

    def exec(self, query, params=()):
        """Ejecuta una consulta que modifica la base de datos."""
        if self.conn is None:
            raise Exception("No se puede ejecutar el comando 'exec' con una base de datos cerrada.")
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f'Error al ejecutar la consulta: {str(e)}. Query: {query}, Parámetros: {params}')

    def select(self, query, params=()):
        """Ejecuta una consulta que devuelve resultados."""
        if self.conn is None:
            raise Exception("No se puede ejecutar el comando 'select' con una base de datos cerrada.")
        try:
            self.cursor.execute(query, params)
            result = self.cursor.fetchall()
            return result
        except sqlite3.Error as e:
            self.conn.rollback()
            # Log error message
            logger.error(f'Error al ejecutar la consulta de selección: {str(e)}. Query: {query}, Parámetros: {params}')
            return None

    def add_column(self, table_name, column_name, column_type):
        """Agrega una columna a una tabla existente """
        query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        self.exec(query)

    ############################################################################
    # Tablas de videos de Youtube
    ############################################################################
    def create_video_tables(self):
        """
        Crea las tablas relacionadas con los videos de YouTube.
        """
        try:
            query = '''
            CREATE TABLE IF NOT EXISTS VIDEO (
                VIDEO_ID TEXT PRIMARY KEY,
                VIDEO_NAME TEXT,
                CHANNEL_ID TEXT,
                VIDEO_LEN TEXT,
                TAGS TEXT,
                PUBLISH_DATE DATE,
                UPDATE_DATE DATE
            )
            '''
            self.exec(query)
        except sqlite3.Error as e:
            logger.error(f'Error al crear la tabla VIDEO: {str(e)}. Query: {query}')
        except Exception as e:
            logger.error(f'Error inesperado al crear la tabla VIDEO: {str(e)}. Query: {query}')

        try:
            query = '''
            CREATE TABLE IF NOT EXISTS VIDEO_RECORDS (
                RECORD_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                VIDEO_ID TEXT,
                VIEWS INTEGER,
                MOST_VIEWED_MOMENT TEXT,
                LIKES INTEGER,
                COMMENTS_COUNT INTEGER,
                UPDATE_DATE DATE
            )
            '''
            self.exec(query)
        except sqlite3.Error as e:
            logger.error(f'Error al crear la tabla VIDEO_RECORDS: {str(e)}. Query: {query}')
        except Exception as e:
            logger.error(f'Error inesperado al crear la tabla VIDEO_RECORDS: {str(e)}. Query: {query}')
    
    def insert_video_record(self, video_info):
        """
        Inserta un registro de video en las tablas correspondientes.
        """
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        try:
            query = '''
            INSERT OR REPLACE INTO VIDEO (
                VIDEO_ID, VIDEO_NAME, CHANNEL_ID, VIDEO_LEN, TAGS, PUBLISH_DATE, UPDATE_DATE
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            '''
            params = (
                video_info['video_id'], video_info['title'], video_info['channel_id'],
                video_info['length'], video_info['tags'], video_info['publish_date'],
                current_time
            )
            self.exec(query, params)
        except sqlite3.Error as e:
            logger.error(f'Error al insertar/actualizar registros en la tabla VIDEO: {str(e)}. Query: {query}, Parámetros: {params}')
        except Exception as e:
            logger.error(f'Error inesperado al insertar/actualizar registros en la tabla VIDEO: {str(e)}. Query: {query}, Parámetros: {params}')

        try:
            query = '''
            INSERT INTO VIDEO_RECORDS (
                VIDEO_ID, VIEWS, MOST_VIEWED_MOMENT, LIKES, COMMENTS_COUNT, UPDATE_DATE
            ) VALUES (?, ?, ?, ?, ?, ?)
            '''
            params = (
                video_info['video_id'], video_info['views'], video_info['mvm'],
                video_info['likes'], video_info['comment_count'],
                current_time
            )
            self.exec(query, params)
        except sqlite3.Error as e:
            logger.error(f'Error al insertar/actualizar registros en la tabla VIDEO_RECORDS: {str(e)}. Query: {query}, Parámetros: {params}')
        except Exception as e:
            logger.error(f'Error inesperado al insertar/actualizar registros en la tabla VIDEO_RECORDS: {str(e)}. Query: {query}, Parámetros: {params}')

    ############################################################################
    # Tablas de shorts de Youtube
    ############################################################################
    def create_short_tables(self):
        """
        Crea las tablas relacionadas con los shorts de YouTube.
        """
        try:
            query = '''
            CREATE TABLE IF NOT EXISTS SHORT (
                SHORT_ID TEXT PRIMARY KEY,
                SHORT_NAME TEXT,
                CHANNEL_ID TEXT,
                SHORT_LEN TEXT,
                TAGS TEXT,
                PUBLISH_DATE DATE,
                UPDATE_DATE DATE
            )
            '''
            self.exec(query)
        except sqlite3.Error as e:
            logger.error(f'Error al crear la tabla SHORT_ID: {str(e)}. Query: {query}')
        except Exception as e:
            logger.error(f'Error inesperado al crear la tabla SHORT_ID: {str(e)}. Query: {query}')

        try:
            query = '''
            CREATE TABLE IF NOT EXISTS SHORT_RECORDS (
                RECORD_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                SHORT_ID TEXT,
                VIEWS INTEGER,
                MOST_VIEWED_MOMENT TEXT,
                LIKES INTEGER,
                COMMENTS_COUNT INTEGER,
                UPDATE_DATE DATE
            )
            '''
            self.exec(query)
        except sqlite3.Error as e:
            logger.error(f'Error al crear la tabla SHORT_ID_RECORDS: {str(e)}. Query: {query}')
        except Exception as e:
            logger.error(f'Error inesperado al crear la tabla SHORT_ID_RECORDS: {str(e)}. Query: {query}')
    
    def insert_short_record(self, short_info):
        """
        Inserta un registro de short en las tablas correspondientes.
        """
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        try:
            query = '''
            INSERT OR REPLACE INTO SHORT (
                SHORT_ID, SHORT_NAME, CHANNEL_ID, SHORT_LEN, TAGS, PUBLISH_DATE, UPDATE_DATE
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            '''
            params = (
                short_info['short_id'], short_info['title'], short_info['channel_id'],
                short_info['length'], short_info['tags'], short_info['publish_date'],
                current_time
            )
            self.exec(query, params)
        except sqlite3.Error as e:
            logger.error(f'Error al insertar/actualizar registros en la tabla SHORT: {str(e)}. Query: {query}, Parámetros: {params}')
        except Exception as e:
            logger.error(f'Error inesperado al insertar/actualizar registros en la tabla SHORT: {str(e)}. Query: {query}, Parámetros: {params}')

        try:
            query = '''
            INSERT INTO SHORT_RECORDS (
                SHORT_ID, VIEWS, MOST_VIEWED_MOMENT, LIKES, COMMENTS_COUNT, UPDATE_DATE
            ) VALUES (?, ?, ?, ?, ?, ?)
            '''
            params = (
                short_info['short_id'], short_info['views'], short_info['mvm'],
                short_info['likes'], short_info['comment_count'],
                current_time
            )
            self.exec(query, params)
        except sqlite3.Error as e:
            logger.error(f'Error al insertar/actualizar registros en la tabla SHORT_RECORDS: {str(e)}. Query: {query}, Parámetros: {params}')
        except Exception as e:
            logger.error(f'Error inesperado al insertar/actualizar registros en la tabla SHORT_RECORDS: {str(e)}. Query: {query}, Parámetros: {params}')

    #################################################################
    # Tablas de canales de Youtube
    #################################################################
    def create_channel_tables(self):
        """
        Crea las tablas relacionadas con los canales de YouTube.
        """
        try:
            query = '''
            CREATE TABLE IF NOT EXISTS CHANNEL (
                CHANNEL_ID TEXT PRIMARY KEY,
                CHANNEL_NAME TEXT,
                UPDATE_DATE DATE
            )
            '''
            self.exec(query)
        except sqlite3.Error as e:
            logger.error(f'Error al crear la tabla CHANNEL: {str(e)}. Query: {query}')
        except Exception as e:
            logger.error(f'Error inesperado al crear la tabla CHANNEL: {str(e)}. Query: {query}')

        try:
            query = '''
            CREATE TABLE IF NOT EXISTS CHANNEL_RECORDS (
                RECORD_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                CHANNEL_ID TEXT,
                VIDEOS_COUNT INTEGER,
                SUBSCRIBERS INTEGER,
                TOTAL_VIEWS INTEGER,
                MONTHLY_SUBS INTEGER,
                DAILY_SUBS INTEGER,
                UPDATE_DATE DATE
            )
            '''
            self.exec(query)
        except sqlite3.Error as e:
            logger.error(f'Error al crear la tabla CHANNEL_RECORDS: {str(e)}. Query: {query}')
        except Exception as e:
            logger.error(f'Error inesperado al crear la tabla CHANNEL_RECORDS: {str(e)}. Query: {query}')

    def insert_channel_record(self, channel_info):
        """
        Inserta un registro de canal en las tablas correspondientes.
        """
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        try:
            query = '''
            INSERT OR REPLACE INTO CHANNEL (
                CHANNEL_ID, CHANNEL_NAME, UPDATE_DATE
            ) VALUES (?, ?, ?)
            '''
            params = (
                channel_info['channel_id'], channel_info['channel_name'],
                current_time
            )
            self.exec(query, params)
        except sqlite3.Error as e:
            logger.error(f'Error al insertar/actualizar registros en la tabla CHANNEL: {str(e)}. Query: {query}, Parámetros: {params}')
        except Exception as e:
            logger.error(f'Error inesperado al insertar/actualizar registros en la tabla CHANNEL: {str(e)}. Query: {query}, Parámetros: {params}')

        try:
            query = '''
            INSERT INTO CHANNEL_RECORDS (
                CHANNEL_ID, VIDEOS_COUNT, SUBSCRIBERS, TOTAL_VIEWS, MONTHLY_SUBS, DAILY_SUBS, UPDATE_DATE
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            '''
            params = (
                channel_info['channel_id'], channel_info['n_videos'], channel_info['subscribers'], channel_info['channel_views'],
                channel_info['monthly_subs'], channel_info['daily_subs'],
                current_time
            )
            self.exec(query, params)
        except sqlite3.Error as e:
            logger.error(f'Error al insertar/actualizar registros en la tabla CHANNEL_RECORDS: {str(e)}. Query: {query}, Parámetros: {params}')
        except Exception as e:
            logger.error(f'Error inesperado al insertar/actualizar registros en la tabla CHANNEL_RECORDS: {str(e)}. Query: {query}, Parámetros: {params}')

    #################################################################
    # Tablas de playlists de Youtube
    #################################################################
    def create_playlist_tables(self):
        """
        Crea las tablas relacionadas con los canales de YouTube.
        """
        try:
            query = '''
            CREATE TABLE IF NOT EXISTS PLAYLIST (
                PLAYLIST_ID TEXT PRIMARY KEY,
                PLAYLIST_NAME TEXT,
                CHANNEL_ID TEXT,
                PUBLISH_DATE DATE,
                UPDATE_DATE DATE
            )
            '''
            self.exec(query)
        except sqlite3.Error as e:
            logger.error(f'Error al crear la tabla PLAYLIST: {str(e)}. Query: {query}')
        except Exception as e:
            logger.error(f'Error inesperado al crear la tabla PLAYLIST: {str(e)}. Query: {query}')

        try:
            query = '''
            CREATE TABLE IF NOT EXISTS PLAYLIST_RECORDS (
                RECORD_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                PLAYLIST_ID TEXT,
                VIDEOS_COUNT INTEGER,
                TOTAL_VIEWS INTEGER,
                LIKES INTEGER,
                UPDATE_DATE DATE
            )
            '''
            self.exec(query)
        except sqlite3.Error as e:
            logger.error(f'Error al crear la tabla PLAYLIST_RECORDS: {str(e)}. Query: {query}')
        except Exception as e:
            logger.error(f'Error inesperado al crear la tabla PLAYLIST_RECORDS: {str(e)}. Query: {query}')
            
        try:
            query = '''
            CREATE TABLE IF NOT EXISTS PLAYLIST_VIDEO (
                PLAYLIST_ID TEXT,
                VIDEO_ID TEXT,
                UPDATE_DATE DATE,
                PRIMARY KEY (PLAYLIST_ID, VIDEO_ID)
            )
            '''
            self.exec(query)
        except sqlite3.Error as e:
            logger.error(f'Error al crear la tabla PLAYLIST_VIDEO: {str(e)}. Query: {query}')
        except Exception as e:
            logger.error(f'Error inesperado al crear la tabla PLAYLIST_VIDEO: {str(e)}. Query: {query}')

    def insert_playlist_record(self, playlist_info):
        """
        Inserta un registro de canal en las tablas correspondientes.
        """
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            query = '''
            INSERT OR REPLACE INTO PLAYLIST (
                PLAYLIST_ID, PLAYLIST_NAME, CHANNEL_ID, PUBLISH_DATE, UPDATE_DATE
            ) VALUES (?, ?, ?, ?, ?)
            '''
            params = (
                playlist_info['playlist_id'], playlist_info['title'], playlist_info['channel_id'], playlist_info['publish_date'],
                current_time
            )
            self.exec(query, params)
        except sqlite3.Error as e:
            logger.error(f'Error al insertar/actualizar registros en la tabla PLAYLIST: {str(e)}. Query: {query}, Parámetros: {params}')
        except Exception as e:
            logger.error(f'Error inesperado al insertar/actualizar registros en la tabla PLAYLIST: {str(e)}. Query: {query}, Parámetros: {params}')
            
        try:
            query = '''
            INSERT INTO PLAYLIST_RECORDS (
                PLAYLIST_ID, VIDEOS_COUNT, TOTAL_VIEWS, LIKES, UPDATE_DATE
            ) VALUES (?, ?, ?, ?, ?)
            '''
            params = (
                playlist_info['playlist_id'], playlist_info['n_videos'], playlist_info['views'], playlist_info['likes'], 
                current_time
            )
            self.exec(query, params)
        except sqlite3.Error as e:
            logger.error(f'Error al insertar/actualizar registros en la tabla PLAYLIST_RECORDS: {str(e)}. Query: {query}, Parámetros: {params}')
        except Exception as e:
            logger.error(f'Error inesperado al insertar/actualizar registros en la tabla PLAYLIST_RECORDS: {str(e)}. Query: {query}, Parámetros: {params}')
        
        try:
            for video_id in playlist_info['video_ids']:
                query = '''
                INSERT INTO PLAYLIST_VIDEO (
                    PLAYLIST_ID, VIDEO_ID, UPDATE_DATE
                ) VALUES (?, ?, ?)
                ON CONFLICT(PLAYLIST_ID, VIDEO_ID)
                DO UPDATE SET UPDATE_DATE = excluded.UPDATE_DATE
                '''
                params = (
                    playlist_info['playlist_id'], video_id,
                    current_time
                )
                self.exec(query, params)
        except sqlite3.Error as e:
            logger.error(f'Error al insertar/actualizar registros en la tabla PLAYLIST_VIDEO: {str(e)}. Query: {query}, Parámetros: {params}')
        except Exception as e:
            logger.error(f'Error inesperado al insertar/actualizar registros en la tabla PLAYLIST_VIDEO: {str(e)}. Query: {query}, Parámetros: {params}')

    #################################################################
    # Tablas de paginas de SimilarWeb
    #################################################################
    def create_similarweb_tables(self):
        """
        Crea las tablas relacionadas con los datos de SimilarWeb.
        """
        try:
            query = '''
            CREATE TABLE IF NOT EXISTS SIMILARWEB_DOMAINS (
                DOMAIN_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                DOMAIN TEXT,
                COMPANY TEXT,
                YEAR_FOUNDER INTEGER,
                EMPLOYEES TEXT,
                HQ TEXT,
                ANNUAL_REVENUE TEXT,
                INDUSTRY TEXT,
                UPDATE_DATE DATE
            )
            '''
            self.exec(query)
        except sqlite3.Error as e:
            logger.error(f'Error al crear la tabla SIMILARWEB_DOMAINS: {str(e)}. Query: {query}')
        except Exception as e:
            logger.error(f'Error inesperado al crear la tabla SIMILARWEB_DOMAINS: {str(e)}. Query: {query}')

        try:
            query = '''
            CREATE TABLE IF NOT EXISTS SIMILARWEB_RECORDS (
                RECORD_ID INTEGER PRIMARY KEY,
                DOMAIN_ID INTEGER,
                GLOBAL_RANK INTEGER,
                COUNTRY_RANK INTEGER,
                CATEGORY_RANK INTEGER,
                TOTAL_VISITS TEXT,
                BOUNCE_RATE INTEGER,
                PAGES_PER_VISIT NUMBER,
                AVG_DURATION_VISIT TEXT,
                UPDATE_DATE DATE
            )
            '''
            self.exec(query)
        except sqlite3.Error as e:
            logger.error(f'Error al crear la tabla SIMILARWEB_RECORDS: {str(e)}. Query: {query}')
        except Exception as e:
            logger.error(f'Error inesperado al crear la tabla SIMILARWEB_RECORDS: {str(e)}. Query: {query}')

    def insert_similarweb_record(self, data):
        """
        Inserta un registro de datos de SimilarWeb en las tablas correspondientes.
        """
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        try:
            query = '''
            INSERT OR REPLACE INTO SIMILARWEB_DOMAINS (
                DOMAIN_ID, DOMAIN, COMPANY, YEAR_FOUNDER, EMPLOYEES, HQ, ANNUAL_REVENUE, INDUSTRY, UPDATE_DATE
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (
                data['domain_id'], data['domain'],
                data['company'], data['year_founder'], data['employees'],
                data['hq'], data['annual_revenue'], data['industry'],
                current_time
            )
            self.exec(query, params)
        except sqlite3.Error as e:
            logger.error(f'Error al insertar/actualizar registros en la tabla SIMILARWEB_DOMAINS: {str(e)}. Query: {query}, Parámetros: {params}')
        except Exception as e:
            logger.error(f'Error inesperado al insertar/actualizar registros en la tabla SIMILARWEB_DOMAINS: {str(e)}. Query: {query}, Parámetros: {params}')

        try:
            query = '''
            INSERT OR REPLACE INTO SIMILARWEB_RECORDS (
                DOMAIN_ID, GLOBAL_RANK, COUNTRY_RANK, CATEGORY_RANK, TOTAL_VISITS, BOUNCE_RATE, PAGES_PER_VISIT, AVG_DURATION_VISIT, UPDATE_DATE
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (
                data['domain_id'],
                data['global_rank'], data['country_rank'], data['category_rank'],
                data['total_visits'], data['bounce_rate'], data['pages_per_visit'],
                data['avg_duration_visit'],
                current_time
            )
            self.exec(query, params)
        except sqlite3.Error as e:
            logger.error(f'Error al insertar/actualizar registros en la tabla SIMILARWEB_RECORDS: {str(e)}. Query: {query}, Parámetros: {params}')
        except Exception as e:
            logger.error(f'Error inesperado al insertar/actualizar registros en la tabla SIMILARWEB_RECORDS: {str(e)}. Query: {query}, Parámetros: {params}')

    #################################################################
    # Tablas de noticias
    #################################################################
    def create_news_tables(self):
        """
        Crea las tablas relacionadas con las noticias.
        """
        try:
            query = '''
            CREATE TABLE IF NOT EXISTS NEWS (
                NEW_ID INTEGER PRIMARY KEY,
                TITLE TEXT,
                TOPIC_ID INTEGER,
                NEWSPAPER_ID INTEGER,
                URL TEXT,
                PUBLISH_DATE DATE,
                ANTIQUE TEXT,
                UPDATE_DATE DATE
            );
            '''
            self.exec(query)
        except sqlite3.Error as e:
            logger.error(f'Error al crear la tabla NEWS: {str(e)}. Query: {query}')
        except Exception as e:
            logger.error(f'Error inesperado al crear la tabla NEWS: {str(e)}. Query: {query}')

        try:
            query = '''
            CREATE TABLE IF NOT EXISTS TOPICS (
                TOPIC_ID INTEGER PRIMARY KEY,
                TOPIC TEXT,
                TOPIC_NEWS INTEGER,
                UPDATE_DATE DATE
            );
            '''
            self.exec(query)
        except sqlite3.Error as e:
            logger.error(f'Error al crear la tabla TOPICS: {str(e)}. Query: {query}')
        except Exception as e:
            logger.error(f'Error inesperado al crear la tabla TOPICS: {str(e)}. Query: {query}')

        try:
            query = '''
            CREATE TABLE IF NOT EXISTS NEWSPAPERS (
                NEWSPAPER_ID INTEGER PRIMARY KEY,
                NEWSPAPER TEXT,
                NEWS_COUNT INTEGER,
                UPDATE_DATE DATE
            );
            '''
            self.exec(query)
        except sqlite3.Error as e:
            logger.error(f'Error al crear la tabla NEWSPAPERS: {str(e)}. Query: {query}')
        except Exception as e:
            logger.error(f'Error inesperado al crear la tabla NEWSPAPERS: {str(e)}. Query: {query}')

    def insert_news_record(self, data):
        """
        Inserta un registro de noticia en las tablas correspondientes.
        """
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        try:
            query = '''
            INSERT OR REPLACE INTO NEWS (
                NEW_ID, TITLE, TOPIC_ID, NEWSPAPER_ID, URL, PUBLISH_DATE, ANTIQUE, UPDATE_DATE
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (
                data['new_id'], data['title'], data['topic_id'],
                data['newspaper_id'], data['url'], data['publish_date'],
                data['antique'], current_time
            )
            self.exec(query, params)
        except sqlite3.Error as e:
            logger.error(f'Error al insertar/actualizar registros en la tabla NEWS: {str(e)}. Query: {query}, Parámetros: {params}')
        except Exception as e:
            logger.error(f'Error inesperado al insertar/actualizar registros en la tabla NEWS: {str(e)}. Query: {query}, Parámetros: {params}')

        try:
            query = '''
            INSERT OR REPLACE INTO TOPICS (
                TOPIC_ID, TOPIC, TOPIC_NEWS, UPDATE_DATE
            ) VALUES (?, ?, ?, ?)
            '''
            params = (
                data['topic_id'], data['topic'], 1, current_time
            )
            self.exec(query, params)
        except sqlite3.Error as e:
            logger.error(f'Error al insertar/actualizar registros en la tabla TOPICS: {str(e)}. Query: {query}, Parámetros: {params}')
        except Exception as e:
            logger.error(f'Error inesperado al insertar/actualizar registros en la tabla TOPICS: {str(e)}. Query: {query}, Parámetros: {params}')

        try:
            query = '''
            INSERT OR REPLACE INTO NEWSPAPERS (
                NEWSPAPER_ID, NEWSPAPER, NEWS_COUNT, UPDATE_DATE
            ) VALUES (?, ?, ?, ?)
            '''
            params = (
                data['newspaper_id'], data['newspaper'], 1, current_time
            )
            self.exec(query, params)
        except sqlite3.Error as e:
            logger.error(f'Error al insertar/actualizar registros en la tabla NEWSPAPERS: {str(e)}. Query: {query}, Parámetros: {params}')
        except Exception as e:
            logger.error(f'Error inesperado al insertar/actualizar registros en la tabla NEWSPAPERS: {str(e)}. Query: {query}, Parámetros: {params}')

    #################################################################
    # Tablas de productos
    #################################################################
    def create_product_tables(self):
        """
        Crea las tablas relacionadas con los productos.
        """
        try:
            query = '''
            CREATE TABLE IF NOT EXISTS PRODUCT (
                PRODUCT_ID TEXT PRIMARY KEY,
                NAME TEXT,
                DESCRIPTION TEXT,
                PLATFORM TEXT,
                STORE TEXT,
                URL TEXT,
                UPDATE_DATE DATE
            );
            '''
            self.exec(query)
        except sqlite3.Error as e:
            logger.error(f'Error al crear la tabla PRODUCT: {str(e)}. Query: {query}')
        except Exception as e:
            logger.error(f'Error inesperado al crear la tabla PRODUCT: {str(e)}. Query: {query}')

        try:
            query = '''
            CREATE TABLE IF NOT EXISTS PRODUCT_RECORDS (
                PRODUCT_ID TEXT PRIMARY KEY,
                PRICE NUMBER,
                CUOTAS INTEGER,
                CURRENCY TEXT,
                RANK INTEGER,
                RATING NUMBER,
                RATE_COUNT INTEGER,
                MOST_SELLED INTEGER,
                PROMOTED INTEGER,
                UPDATE_DATE DATE
            );
            '''
            self.exec(query)
        except sqlite3.Error as e:
            logger.error(f'Error al crear la tabla PRODUCT_RECORDS: {str(e)}. Query: {query}')
        except Exception as e:
            logger.error(f'Error inesperado al crear la tabla PRODUCT_RECORDS: {str(e)}. Query: {query}')

    def insert_product_record(self, data={}):
        """
        Inserta un registro de producto en las tablas correspondientes.
        """
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        try:
            query = '''
            INSERT OR REPLACE INTO PRODUCT (
                PRODUCT_ID, NAME, DESCRIPTION, PLATFORM, STORE, URL, UPDATE_DATE
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            '''
            params = (
                data['product_id'], data['product_name'], data['description'],
                data['platform'], data['store'], data['url'], current_time
            )
            self.exec(query, params)
        except sqlite3.Error as e:
            logger.error(f'Error al insertar/actualizar registros en la tabla PRODUCT: {str(e)}. Query: {query}, Parámetros: {params}')
        except Exception as e:
            logger.error(f'Error inesperado al insertar/actualizar registros en la tabla PRODUCT: {str(e)}. Query: {query}, Parámetros: {params}')

        try:
            query = '''
            INSERT OR REPLACE INTO PRODUCT_RECORDS (
                PRODUCT_ID, PRICE, CUOTAS, CURRENCY, RANK, RATING, RATE_COUNT, MOST_SELLED, PROMOTED, UPDATE_DATE
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (
                data['product_id'], data['price'], data['installments'], data['currency'],
                data['ranking'], data['rating'], data['rating_count'],
                data['is_best_seller'], data['is_promoted'], current_time
            )
            self.exec(query, params)
        except sqlite3.Error as e:
            logger.error(f'Error al insertar/actualizar registros en la tabla PRODUCT_RECORDS: {str(e)}. Query: {query}, Parámetros: {params}')
        except Exception as e:
            logger.error(f'Error inesperado al insertar/actualizar registros en la tabla PRODUCT_RECORDS: {str(e)}. Query: {query}, Parámetros: {params}')

    #################################################################
    # Exportacion de tablas
    #################################################################
    def export_table(self, path='results/db/', ext='.csv'):
        """
        Exporta las tablas especificadas a archivos en el formato indicado.

        Parámetros:
        path (str): Directorio donde se guardarán los archivos exportados.
        ext (str): Extensión del archivo de exportación (.csv o .xlsx).
        """
        table_names = [
            'VIDEO', 'VIDEO_RECORDS', 'CHANNEL', 'CHANNEL_RECORDS',
            'SHORT','SHORT_RECORDS','PLAYLIST','PLAYLIST_RECORDS','PLAYLIST_VIDEO',
            'NEWS', 'NEWSPAPERS', 'SIMILARWEB_DOMAINS', 'SIMILARWEB_RECORDS', 'TOPICS',
            'PRODUCT', 'PRODUCT_RECORDS'
        ]

        # Asegurarse de que el directorio de destino exista
        os.makedirs(path, exist_ok=True)

        for table_name in table_names:
            # Paso el nombre de la tabla a minúsculas
            table_name_lower = table_name.lower()

            try:
                # Nombre de la tabla a exportar
                query = f"SELECT * FROM {table_name_lower}"
                
                # Obtengo los datos de la tabla
                df = pd.read_sql_query(query, self.conn)

                # Si la tabla está vacía, se omite la exportación
                if df.empty:
                    logger.info(f'La tabla {table_name} está vacía. No se exportará.')
                    continue

                # Crea la columna "ID Fecha" con el formato YYYYMMDD
                # Cuando se utiliza errors='coerce', cualquier valor que no se
                # pueda convertir a un objeto datetime será convertido en
                # NaT (Not a Time), que es la representación de pandas para
                # fechas faltantes o no válidas.
                df['UPDATE_DATE'] = pd.to_datetime(df['UPDATE_DATE'], errors='coerce')
                df['ID Fecha'] = df['UPDATE_DATE'].apply(lambda x: x.strftime('%Y%m%d') if not pd.isnull(x) else '')

                # Defino el tipo de exportación
                if ext == '.csv':
                    filename = f'{path}/{table_name_lower}.csv'
                    df.to_csv(filename, index=False)
                elif ext == '.xlsx':
                    filename = f'{path}/{table_name_lower}.xlsx'
                    df.to_excel(filename, index=False)
                else:
                    logger.error(f'Formato no válido: {ext}')
                    return

                logger.info(f"Datos de la tabla '{table_name}' exportados a '{filename}'.")

            except sqlite3.Error as e:
                logger.error(f'Error al consultar la tabla {table_name}: {e}. Query: {query}')
            except Exception as e:
                logger.error(f'Error inesperado al exportar la tabla {table_name}: {e}')

    #############################################################
    # Especific functions
    #############################################################    
    def get_youtube_channel_data(self, target='CHANNEL_ID', table_name='CHANNEL', sort='desc'):
        """
        Obtiene una lista de IDs de canales de YouTube de la tabla especificada.

        Parámetros:
        table_name (str): Nombre de la tabla a consultar.
        sort (str): Orden de los resultados, 'asc' para ascendente o 'desc' para descendente.

        Retorna:
        list: Lista de IDs de canales.
        """
        query = f'SELECT DISTINCT {target} FROM {table_name}'
        if sort == 'asc':
            query += ' ORDER BY UPDATE_DATE ASC'
        elif sort == 'desc':
            query += ' ORDER BY UPDATE_DATE DESC'
        else:
            logger.warning(f'Orden no válido: {sort}. Usando el valor por defecto "desc".')
            query += ' ORDER BY UPDATE_DATE DESC'

        try:
            db_ids = self.select(query, ())
            db_ids = [item[0] for item in db_ids]
            return db_ids
        except Exception as e:
            logger.error(f'Error al obtener IDs de canales de la tabla {table_name}. Error: {str(e)}')
            return []

    def get_youtube_video_ids(self, table_name='VIDEO', sort='desc', channel_id_list=None):
        """
        Obtiene una lista de IDs de videos de YouTube de la tabla especificada.

        Parámetros:
        table_name (str): Nombre de la tabla a consultar.
        sort (str): Orden de los resultados, 'asc' para ascendente o 'desc' para descendente.
        channel_id (str): Lista de canales para aplicar el filtrado

        Retorna:
        list: Lista de IDs de canales.
        """
        query = f'SELECT DISTINCT VIDEO_ID FROM {table_name}'
        if channel_id_list:
            query += ' WHERE CHANNEL_ID IN ("{}")'.format(join_str(channel_id_list))
        if sort == 'asc':
            query += ' ORDER BY UPDATE_DATE ASC'
        elif sort == 'desc':
            query += ' ORDER BY UPDATE_DATE DESC'
        else:
            logger.warning(f'Orden no válido: {sort}. Usando el valor por defecto "desc".')
            query += ' ORDER BY UPDATE_DATE DESC'

        try:
            db_ids = self.select(query, ())
            db_ids = [item[0] for item in db_ids]
            return db_ids
        except Exception as e:
            logger.error(f'Error al obtener IDs de videos de la tabla {table_name}. Error: {str(e)}')
            return []
        
    def get_similar_domains(self, target='DOMAIN', table_name='SIMILARWEB_DOMAINS', sort='asc'):
        """
        Obtiene una lista de dominios únicos de la tabla especificada.

        Parámetros:
        table_name (str): Nombre de la tabla a consultar.
        sort (str): Orden de los resultados, 'asc' para ascendente o 'desc' para descendente.

        Retorna:
        list: Lista de dominios únicos.
        """
        query = f'SELECT DISTINCT {target} FROM {table_name}'
        if sort == 'asc':
            query += ' ORDER BY domain ASC'
        elif sort == 'desc':
            query += ' ORDER BY domain DESC'
        else:
            logger.warning(f'Orden no válido: {sort}. Usando el valor por defecto "asc".')
            query += ' ORDER BY domain ASC'

        try:
            query_res = self.select(query)
            domains = [x[0] for x in query_res]
            return domains
        except Exception as e:
            logger.error(f'Error al obtener dominios de la tabla {table_name}. Error: {str(e)}')
            return []
        
    def get_topics(self):
        """
        Obtiene una lista de las tematicas a abordar por el proyecto.

        Parámetros:

        Retorna:
        list: Lista de temáticas únicas.
        """
        query = 'SELECT TOPIC FROM TOPICS'
        results = self.select(query)
        try:
            return [x[0] for x in results]
        except Exception as e:
            logger.error(f'Error al obtener las temáticas desde la tabla TOPICS. Error: {str(e)}')
            return []

    def process_data(self, op='select', type=None, sel='name', val='elxokas'):
        """
        Procesa los datos basados en los parámetros proporcionados.

        Parámetros:
        op (str): Operación a realizar, 'select' para seleccionar o 'del' para eliminar.
        type (str): Tipo de datos, 'video' o 'channel'.
        sel (str): Criterio de selección, 'id', 'name', '-channelid' o '-channelname'.
        val (str): Valor a buscar.

        Retorna:
        None
        """
        if type not in ['video', 'channel']:
            logger.error('Opciones válidas para type: {channel/video}')
            return

        query = None
        if type == 'video':
            if sel == 'id':
                query = f"SELECT * FROM VIDEO WHERE VIDEO_ID LIKE ?"
            elif sel == 'name':
                query = f"SELECT * FROM VIDEO WHERE VIDEO_NAME LIKE ?"
            elif sel == '-channelid':
                query = f"SELECT * FROM VIDEO WHERE CHANNEL_ID LIKE ?"
            elif sel == '-channelname':
                query = f"""
                    SELECT * FROM VIDEO 
                    WHERE CHANNEL_ID = (
                        SELECT CHANNEL_ID FROM CHANNEL WHERE CHANNEL_NAME LIKE ?
                    )
                """
        elif type == 'channel':
            if sel == 'id':
                query = f"SELECT * FROM CHANNEL WHERE CHANNEL_ID LIKE ?"
            elif sel == 'name':
                query = f"SELECT * FROM CHANNEL WHERE CHANNEL_NAME LIKE ?"

        if query is None:
            logger.error('Criterios válidos para sel: {id/name/-channelid/-channelname}')
            return

        # Imprimir consulta ejecutada
        logger.info(f'\nExecuted query:\n{query}\n')

        # Ejecutar consulta y obtener resultados
        try:
            results = self.select(query, (f'%{val}%',))
            if not results:
                logger.info('No results.')
                return
            else:
                for kk, result in enumerate(results):
                    logger.info(f'{kk}: {result}')
        except Exception as e:
            logger.error(f'Error al ejecutar la consulta: {str(e)}')
            return

        # Eliminar resultados si se especifica
        if op == 'del':
            ans = input('\nWARNING! You are about to delete the results above\nContinue? (y/n): ').lower()
            if ans == 'y':
                try:
                    del_query = query.replace('SELECT *', 'DELETE')
                    self.exec(del_query, (f'%{val}%',))
                    logger.info('Results deleted.')
                except Exception as e:
                    logger.error(f'Error al eliminar los resultados: {str(e)}')

if __name__ == '__main__':
    db = Database()

    # Add column
    db.add_column('CHANNEL_RECORDS', 'SUBSCRIBERS', 'INTEGER')