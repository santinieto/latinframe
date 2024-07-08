def configure_app(app):
    app.screen()  # Limpia la pantalla
    app.add_option("Opción 1", lambda: print("Opción 1 seleccionada"))
    app.add_option("Opción 2", lambda: print("Opción 2 seleccionada"))
    app.add_user_input("Ingrese texto aquí", lambda app, text: print(f"Texto ingresado: {text}"))
    app.add_option("Volver", lambda: app.main_menu())