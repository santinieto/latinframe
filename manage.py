from src.utils.environment import set_environment
from src.gui.gui import get_app
import src.menus.menu as menu

def main():
    """
    Función principal para crear y ejecutar la aplicación de la interfaz gráfica.
    """
    # Seteo las variables de entorno
    set_environment(filename='settings.json')
    
    try:
        # Creo la App para la interfaz gráfica
        app = get_app()
        app.pack(fill="both", expand=True)

        # Configura el menú principal
        menu.configure_main_menu(app)
        
        # Ejecuto el bucle principal
        app.mainloop()
    except Exception as e:
        print(f"Error en la aplicación principal: {e}")

if __name__ == "__main__":
    main()
