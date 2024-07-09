from src.database.db_fetch import *

def menu_backups(app):
    """
    Configura la pantalla del menú de Resguardos en la aplicación.

    Args:
        app: La instancia de la aplicación de la interfaz gráfica.
    """
    logger.info('Menu de backups de la base de datos.')
    try:
        app.screen()  # Limpia la pantalla
        app.add_option("Generar Backup", lambda: sql_generate_db_backup())
        app.add_option("Restaurar base de datos", lambda: sql_restore_db_backup())
        app.add_option("Volver", lambda: app.main_menu())
    except AttributeError as e:
        print(f"Error al configurar el menú de Resguardos: {e}")