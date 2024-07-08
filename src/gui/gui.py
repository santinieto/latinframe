import tkinter as tk
from tkinter import ttk
import sys, os
from src.utils.utils import getenv
from src.utils.logger import Logger, InfoFormatter, ErrorFormatter
import logging

# Crear un logger
logger = Logger().get_logger()

def get_app():
    root = tk.Tk()
    app = LatinframeGUI(root)
    return app

################################################################################
# Creo una clase con la que voy a imprimir la salida del logger dentr del cuadro
# de texto
################################################################################
class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.config(state='normal')
        self.text_widget.insert(tk.END, msg + '\n')
        self.text_widget.see(tk.END)
        self.text_widget.update_idletasks()  # Force update of the GUI
        
def setup_logging(text_widget, level=logging.DEBUG, formatter=InfoFormatter):
    handler = TextHandler(text_widget)
    handler.setLevel(level)
    handler.setFormatter(formatter())
    logging.getLogger().addHandler(handler)

################################################################################
# Clase principal
################################################################################
class LatinframeGUI(tk.Frame):
    """
    Clase para una interfaz gráfica generalizada con Tkinter.

    Atributos:
        WIDTH (int): Ancho por defecto de la ventana.
        HEIGHT (int): Alto por defecto de la ventana.
    """
    _instance = None
    
    # Definición de colores
    UI_WHITE = '#d8e9f0'  # Color blanco para la interfaz
    UI_GRAY = '#33425b'   # Color gris oscuro para la interfaz
    UI_RED = '#f33535'    # Color rojo para resaltar botones
    UI_BLACK = '#29252c'  # Color negro para textos y elementos oscuros
    
    BG_COLOR = UI_BLACK
    BTN_BG_COLOR = UI_RED
    BTN_FONT_COLOR = UI_WHITE

    def __new__(cls, master=None):
        """
        Crea una única instancia de la clase si aún no existe.
        
        Args:
            master (tk.Tk or tk.Toplevel): Ventana maestra de Tkinter.
            width (int): Ancho de la ventana.
            height (int): Alto de la ventana.
        
        Returns:
            LatinframeGUI: Instancia única de la clase LatinframeGUI.
        """
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, master=None):
        """
        Inicializa la interfaz gráfica.

        Args:
            master (tk.Tk or tk.Toplevel): Ventana maestra de Tkinter.
            width (int): Ancho de la ventana.
            height (int): Alto de la ventana.
        """
        if hasattr(self, 'initialized'):
            return
        self.initialized = True
    
        # Valores por defecto
        self.WIDTH = int(getenv('UI_WIDTH', 1000))
        self.HEIGHT = int(getenv('UI_HEIGHT', 500))
        
        super().__init__(master)
        self.root  = master
        self.root.title("Latinframe Animation Studio")
        self.root.configure(bg=self.BG_COLOR)  # Cambiar color de fondo de la ventana
        self.root.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        
        # Creo el frame para los botones
        self.btns_frame = self.create_frame(side=tk.LEFT, padx=20, pady=20)
        
        # Text el frame para el cuadro de texto
        self.txt_frame = self.create_frame(side=tk.LEFT, padx=20, pady=20)
        
        # Creo el cuadro de texto que va a estar fijo
        self.textbox = self.create_textbox(self.txt_frame, width=40, height=10)

        # Redirigir stdout al widget de texto
        # Creo que no hace 
        sys.stdout = TextRedirector(self.textbox, "stdout")

        # Configurar la salida del Logger
        # Con poner el DEBUG basta porque es el que estoy redirigiendo a la consola
        setup_logging(self.textbox, level=logging.DEBUG, formatter=InfoFormatter)

        # Lista de opciones del menu principal
        self.main_menu_options = []

    ############################################################################
    # Metodos que son llamados internamente dentro de la clase
    ############################################################################
    def create_frame(self, fill=tk.BOTH, side=tk.TOP, padx=10, pady=10, expand=True):
        """
        Crea un frame dentro de la ventana principal con opciones de configuración.

        Args:
        - fill (str, opcional): Dirección en la que el frame se expande para llenar el espacio disponible ('x', 'y', 'both', 'none').
        - side (str, opcional): Lado donde se colocará el frame dentro de la ventana principal ('top', 'bottom', 'left', 'right').
        - padx (int, opcional): Espacio horizontal alrededor del frame.
        - pady (int, opcional): Espacio vertical alrededor del frame.
        - expand (bool, opcional): Si se expande el frame para llenar el espacio disponible.

        Returns:
        - tk.Frame: Instancia del frame creado.
        """
        frame = tk.Frame(self.root, bg=self.BG_COLOR, padx=padx, pady=pady)
        frame.pack(fill=fill, side=side, expand=expand)
        return frame

    def create_button(self, parent, text, command=None, side=tk.TOP, fill=tk.X, padx=5, pady=5, expand=True):
        """
        Crea un botón dentro de un frame con opciones de configuración.

        Args:
        - parent (tk.Widget): Widget padre donde se ubicará el botón.
        - text (str): Texto del botón.
        - command (función, opcional): Función a llamar cuando se presiona el botón.
        - side (str, opcional): Lado donde se colocará el botón dentro del widget padre ('top', 'bottom', 'left', 'right').
        - fill (str, opcional): Dirección en la que el botón se expande para llenar el espacio disponible ('x', 'y', 'both', 'none').
        - padx (int, opcional): Espacio horizontal alrededor del botón.
        - pady (int, opcional): Espacio vertical alrededor del botón.
        - expand (bool, opcional): Si se expande el botón para llenar el espacio disponible.

        Returns:
        - tk.Button: Instancia del botón creado.
        """
        button = tk.Button(parent, text=text, command=command, bg=self.BTN_BG_COLOR, fg=self.BTN_FONT_COLOR)
        button.pack(fill=fill, side=side, padx=padx, pady=pady, expand=expand)
        return button

    def create_entry(self, parent, placeholder='Placeholder', width=30):
        """
        Crea un campo de entrada de texto (Entry widget) dentro del widget padre con opciones de configuración.

        Args:
        - parent (tk.Widget): Widget padre donde se ubicará el campo de entrada.
        - width (int, opcional): Ancho del campo de entrada.

        Returns:
        - tk.Entry: Instancia del campo de entrada creado.
        """
        entry = tk.Entry(parent, width=width, bg=self.UI_WHITE)
        entry.insert(0, placeholder) 
        entry.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        return entry

    def create_label(self, parent, text):
        """
        Crea un label (Label widget) dentro del widget padre con opciones de configuración.

        Args:
        - parent (tk.Widget): Widget padre donde se ubicará el label.
        - text (str): Texto del label.
        - bg (str, opcional): Color de fondo del label.
        - fg (str, opcional): Color del texto del label.

        Returns:
        - tk.Label: Instancia del label creado.
        """
        label = tk.Label(parent, text=text, bg=self.BG_COLOR, fg=self.UI_WHITE)
        label.pack(fill=tk.BOTH, expand=True)
        return label

    def create_textbox(self, parent, width=40, height=10, expand=True):
        """
        Crea un cuadro de texto (Text widget) dentro del widget padre con opciones de configuración.

        Args:
        - parent (tk.Widget): Widget padre donde se ubicará el cuadro de texto.
        - width (int, opcional): Ancho del cuadro de texto.
        - height (int, opcional): Altura del cuadro de texto.
        - expand (bool, opcional): Si se expande el cuadro para llenar el espacio disponible.

        Returns:
        - tk.Text: Instancia del cuadro de texto creado.
        """
        textbox = tk.Text(parent, width=width, height=height, bg=self.UI_GRAY, fg=self.UI_WHITE)
        textbox.pack(fill=tk.BOTH, expand=expand)
        return textbox

    def clear_frame(self, frame):
        """
        Elimina todos los widgets dentro de un frame sin eliminar el frame en sí ni perder su configuración.

        Args:
        - frame (tk.Frame): El frame del cual se eliminarán todos los widgets hijos.
        """
        for widget in frame.winfo_children():
            widget.destroy()
            
    ############################################################################
    # Metodos que son llamados desde afuera de la clase
    ############################################################################
    def main_menu(self):
        # Configure the main menu with the stored options
        self.screen()  # Clear the screen
        for text, command in self.main_menu_options:
            self.add_option(text, command)
            
    def screen(self):
        """
        Limpia la ventana eliminando todos los widgets actuales, excepto el widget de texto.
        """
        self.clear_frame(self.btns_frame)
        
        # Asegura que el frame esté empaquetado
        self.pack()
        
        # Agrego el boton para salir
        self.add_quit_button()

    def add_main_menu_option(self, text, command):
        """
        Agrego opciones al menu principal
        """
        self.main_menu_options.append((text, command))

    def add_option(self, text, command):
        """
        Agrega un botón con el texto y comando proporcionado al frame de botones.

        Args:
            text (str): Texto del botón.
            command (callable): Función que se ejecuta cuando se presiona el botón.
        """
        self.create_button(self.btns_frame, text, command=command)

    def add_label(self, text, **kwargs):
        """
        Agrega una etiqueta con el texto proporcionado al frame de botones.

        Args:
            text (str): Texto de la etiqueta.
            **kwargs: Otros argumentos para personalizar la etiqueta (por ejemplo, font, foreground, etc.).
        """
        self.create_label(self.btns_frame, text=text)

    def add_quit_button(self):
        """
        Agrega un botón para salir de la aplicación al frame de botones.
        """        
        self.create_button(self.btns_frame, text="Salir", side=tk.BOTTOM, command=self.master.destroy)

    def add_user_input(self, placeholder="Placeholder text", submit_command=None, btn_text='Enviar'):
        """
        Agrega un widget de entrada de texto y un botón para operar con el texto ingresado.

        Args:
            placeholder (str): Texto de marcador de posición en el widget de entrada.
            submit_command (callable): Función externa que se llama con el texto ingresado como argumento.
        """
        # Función para manejar el texto ingresado por el usuario
        def handle_input():
            input_text = entry.get()
            if submit_command:
                return submit_command(input_text)  # Llama a la función externa con el texto ingresado
            entry.delete(0, "end")  # Borra el contenido del Entry después de procesar
        
        # Widget de entrada de texto
        entry = self.create_entry(self.btns_frame, placeholder=placeholder, width=30)

        # Botón para capturar el texto ingresado
        self.create_button(self.btns_frame, text=btn_text, command=handle_input)
        
# Clase para redirigir stdout al widget de texto
class TextRedirector:
    """
    Clase para redirigir la salida estándar (stdout) a un widget de texto en una GUI.
    """
    
    def __init__(self, widget, tag="stdout"):
        """
        Inicializa el redireccionador de salida.

        Args:
            widget (tk.Text): Widget de texto donde se redirige la salida.
            tag (str): Etiqueta para identificar la salida en el widget.
        """
        self.widget = widget
        self.tag = tag

    def write(self, msg):
        """
        Escribe el mensaje en el widget de texto con la etiqueta especificada.

        Args:
            msg (str): Mensaje a escribir en el widget de texto.
        """
        self.widget.insert("end", msg, (self.tag,))
        self.widget.see("end")  # Desplaza automáticamente hacia abajo al final del texto

    def flush(self):
        """
        Método de descarga, no realiza ninguna acción.
        """
        pass
    
# Ejemplo de uso de la clase LatinframeGUI
def main():
    app = get_app()

    # Agrega opciones iniciales
    switch_to_main(app)

    app.mainloop()

def switch_to_modules(app):
    app.screen()  # Limpia la pantalla actual
    app.add_label("Seleccione un módulo:")
    app.add_option("Módulo 1", lambda: print("Acción del módulo 1"))
    app.add_option("Módulo 2", lambda: print("Acción del módulo 2"))
    app.add_option("Volver", lambda: switch_to_main(app))

def switch_to_main(app):
    app.screen()  # Limpia la pantalla actual
    app.add_option("Ejecutar todo", lambda: print("Ejecutar todo"))
    app.add_option("Modulos", lambda: switch_to_modules(app))

    # Agrega entrada de texto
    app.add_user_input("Ingrese su nombre:", submit_command=handle_submit)
    
    app.add_quit_button()

# Función externa que se llamará al presionar "Enviar"
def handle_submit(app, text):
    app.textbox.insert("end", f"Texto ingresado: {text}\n")
    
if __name__ == "__main__":
    main()