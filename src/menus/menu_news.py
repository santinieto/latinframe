# Imports estándar de Python
import os
# import sys

# Añade el directorio raíz del proyecto a sys.path
# current_path = os.path.dirname(os.path.abspath(__file__))
# project_root = os.path.abspath(os.path.join(current_path, '..', '..'))  # Ajusta según la estructura de tu proyecto
# sys.path.append(project_root)

# Imports de terceros
# Ninguno en este set

# Imports locales
from src.news.google_news import GoogleNewsListings, fetch_new_id
from src.logger.logger import Logger
from src.database.db import Database

################################################################################
# Genero una instancia del Logger
################################################################################
logger = Logger(os.path.basename(__file__)).get_logger()

def menu_news(app):
    """
    Configura la pantalla del menú de Noticias en la aplicación.

    Args:
        app: La instancia de la aplicación de la interfaz gráfica.
    """
    logger.info('Menu de gestion de noticias.')
    try:
        app.screen()  # Limpia la pantalla
        app.add_option("Actualizar todo", lambda: fetch_all_news_data())
        app.add_option("Tematicas", lambda: fetch_topics())
        app.add_option("Periodicos", lambda: fetch_news_papers())
        app.add_option("Volver", lambda: app.main_menu())
    except AttributeError as e:
        logger.info(f"Error al configurar el menú de Noticias: {e}")

def fetch_all_news_data():
    # Definir la categoría de productos
    topics = [
        'juguetes',
    ]
    topics.append('peliculas infantiles')
    topics.append('amazon')
    topics.append('netflix')
    topics.append('hbo max')
    topics.append('pixar')
    topics.append('pixar elementos')
    topics.append('pixar elemental')
    
    # Obtengo las tematicas desde la base de datos
    with Database('latinframe.db') as db:
        topics = topics + db.get_topics()
    
    google_news_listings = GoogleNewsListings(topics)
    google_news_listings.fetch_data()
    
    # Pido las noticias
    news = google_news_listings.get_news()

    # Guardo los datos
    with Database() as db:
        # Recorro las noticias y les agrego los ID
        # Guardo los datos en la base de datos
        for new in news:
            new.new_id = fetch_new_id(
                id_field='new_id',
                table_name='news',
                search_field='title',
                target=new.title
                )
            new.topic_id = fetch_new_id(
                id_field='topic_id',
                table_name='topics',
                search_field='topic',
                target=new.topic
                )
            new.newspaper_id = fetch_new_id(
                id_field='newspaper_id',
                table_name='newspapers',
                search_field='newspaper',
                target=new.newspaper
                )
            
            # Muestro los datos en pantalla
            logger.info(str(new))

            # Agrego la noticia a la base de datos
            # FIXME: Tengo que ver si se esta guardando bien
            db.insert_news_record( new.to_dicc() )

def fetch_topics():
    with Database('latinframe.db') as db:
        topics = db.get_topics()
        for topic in topics:
            logger.info(topic)
    pass

def fetch_news_papers():
    query = 'SELECT NEWSPAPER FROM NEWSPAPERS'
    with Database('latinframe.db') as db:
        query = 'SELECT TOPIC FROM TOPICS'
        results = db.select(query)
        for result in results:
            logger.info(result[0])