from src.products.product_manager import ProductManager
from src.utils.logger import Logger
from src.database.db import Database

# Crear un logger
logger = Logger().get_logger()

def menu_products(app):
    """
    Configura la pantalla del menú de Productos en la aplicación.

    Args:
        app: La instancia de la aplicación de la interfaz gráfica.
    """
    try:
        app.screen()  # Limpia la pantalla
        app.add_option("Actualizar todo", lambda: fetch_products_data())
        app.add_option("Tematicas", lambda: fetch_topics())
        app.add_option("Prodcutos de Mercado Libre", lambda: fetch_products_data(sel='mercadolibre'))
        app.add_option("Prodcutos de Ebay", lambda: fetch_products_data(sel='ebay'))
        app.add_option("Prodcutos de Alibaba", lambda: fetch_products_data(sel='alibaba'))
        app.add_option("Prodcutos de Amazon", lambda: fetch_products_data(sel='amazon'))
        app.add_option("Volver", lambda: app.main_menu())
    except AttributeError as e:
        print(f"Error al configurar el menú de Productos: {e}")

def fetch_products_data(sel='all'):
    # Definir la categoría de productos
    topics = [
        'juguetes',
    ]
    
    # Obtengo las tematicas desde la base de datos
    with Database('latinframe.db') as db:
        topics = topics + db.get_topics()

    # Creo el objeto unico que gestiona los productos
    product_manager = ProductManager(topics)

    # Lista de funciones para obtener productos
    fetch_functions = {
        'all': product_manager.fetch_products,
        'mercadolibre': product_manager.fetch_meli_products,
        'ebay': product_manager.fetch_ebay_products,
        'alibaba': product_manager.fetch_alibaba_products
    }

    # Variable para verificar si se ha llamado a alguna función de fetch
    called_fetch = False

    for key, fetch_function in fetch_functions.items():
        if sel == key:
            fetch_function()
            called_fetch = True

    if called_fetch:
        # Muestro la informacion
        product_manager.show_items()
        # Guardo los resultados en la base de datos
        product_manager.insert_data_to_db()
        
        messages = {
            'all': 'Se obtuvieron los productos para todas las plataformas.',
            'mercadolibre': 'Se obtuvieron los productos para la plataforma Mercado Libre.',
            'ebay': 'Se obtuvieron los productos para la plataforma Ebay.',
            'alibaba': 'Se obtuvieron los productos para la plataforma Alibaba.'
        }
        
        print(messages[sel])

def fetch_topics():
    with Database('latinframe.db') as db:
        topics = db.get_topics()
        for topic in topics:
            print(topic)
    pass