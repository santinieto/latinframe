def configure_app(app):
    app.screen()  # Limpia la pantalla
    app.add_option("Opción 3", lambda: print("Opción 3 seleccionada"))
    app.add_option("Opción 4", lambda: print("Opción 4 seleccionada"))
    app.add_option("Submodulo 1", lambda: sub_menu_1(app))
    app.add_option("Volver", lambda: app.main_menu())
    
def sub_menu_1(app):
    app.screen()  # Limpia la pantalla
    app.add_option("Prueba", lambda: print("Mensaje de prueba"))
    app.add_label("Ingrese su nombre:")
    app.add_user_input(placeholder = "Juan", submit_command = lambda app, text: print(f"Su nombre es {text}"))
    app.add_option("Volver", lambda: configure_app(app))