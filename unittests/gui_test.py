try:
    from src.gui import get_app, LatinframeGUI
    import src.aux_gui_test_1 as agt1
    import src.aux_gui_test_2 as agt2
except:
    from gui import get_app, LatinframeGUI
    import aux_gui_test_1 as agt1
    import aux_gui_test_2 as agt2

def configure_main_menu(app):
    app.add_main_menu_option("Modulo 1", lambda: agt1.configure_app(app))
    app.add_main_menu_option("Modulo 2", lambda: agt2.configure_app(app))
    app.main_menu()

def main():
    app = get_app()
    app.pack(fill="both", expand=True)

    # Configura el menú principal
    configure_main_menu(app)
    
    app.mainloop()

if __name__ == "__main__":
    main()