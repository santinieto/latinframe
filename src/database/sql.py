# Imports estándar de Python
# import os
# import sys

# Añade el directorio raíz del proyecto a sys.path
# current_path = os.path.dirname(os.path.abspath(__file__))
# project_root = os.path.abspath(os.path.join(current_path, '..', '..'))  # Ajusta según la estructura de tu proyecto
# sys.path.append(project_root)

# Imports de terceros
# No hay librerias

# Imports locales
from src.database.db import Database

def sql_help(script_name, arg):
    print('Usage:')
    print( '\t "-q QUERY" : Execute the given query')
    print( '\t "-f FILENAME" : Execute the given query')

def handle_sql_args(args):
    # Defino un nombre por defecto al modulo
    module_name = 'test'

    # Obtengo el mensaje de ayuda
    if args.ayuda:
        sql_help()

    # Verifico si tengo que leer un archivo
    # Cargo la consulta y la ejecuto
    elif args.file:
        print('SQL - Ejecutar un comando SQL desde un archivo - {}'.format(args.file))
        query = sql_get_query_fromfile(args.file)
        sql_execute(query)

    # Ejecuto el comando SQL
    elif args.query:
        print('SQL - Ejecutar un comando SQL desde consola - {}'.format(args.query))
        sql_execute(args.query)

    # Ejecuto un select sobre la base de datos
    elif args.get:
        with Database() as db:
            db.process_data(op='select',type=args.get[0], sel=args.get[1], val=args.get[2])

    # Ejecuto un select sobre la base de datos
    elif args.select:
        with Database() as db:
            db.process_data(op='select',type=args.select[0], sel=args.select[1], val=args.select[2])

    # Ejecuto un delete sobre la base de datos
    elif args.delete:
        with Database() as db:
            db.process_data(op='del',type=args.delete[0], sel=args.delete[1], val=args.delete[2])

    # Mensaje de error por defecto
    else:
        print(f'Modulos {module_name}')
        print(f'\tSe ha producido un error al procesar el comando')
        print(f'\tPuede utilizar {module_name} -h para obtener ayuda')

def sql_get_query_fromfile(filename):
    """
    Verifico si tengo que leer un archivo
    Ejemplo
    $ python manage.py -sql -file sql/0015_query_1.sql
    """

    # Establezco un valor por defecto para la consulta
    query = ''

    # Trato de obtener la consulta a partir de un archivo
    try:
        with open(filename, "r") as archivo:
            # Lee todo el contenido del archivo y lo almacena en la cadena 'query'
            query = archivo.read()

        # Ahora 'query' contiene el contenido del archivo como una cadena
        # La muestro por pantalla si no hubo errores
        print("SQL query:\n\n" + query)

    # Defino los errores
    except FileNotFoundError:
        print(f"El archivo '{filename}' no fue encontrado.")
    except Exception as e:
        print(f"Ocurrió un error: {e}")

    return query

def sql_execute(query):
    """
    Ejecuto una consulta SQL dada por el usuario teniendo en cuenta
    que si es del caracter SELECT entonces tengo que mostrar los datos
    resultado en pantalla.
    Ejemplo:
    $ python manage.py -sql "select * from channel;"
    """

    # Abro la conexion con la base de datos
    with Database() as db:

        # Obtengo la primer palabra
        fw = query.split()[0].lower()

        # Si es un SELECT tengo que mostrar los resultados
        # Ejemplo:
        # python manage.py -sql "SELECT CHANNEL_ID FROM CHANNEL"
        # python manage.py -sql "SELECT * FROM CHANNEL"
        # python manage.py -sql "select * from channel"
        if fw == 'select':
            results = db.select(query, ())
            for result in results:
                print(result)

        # Si es otro tipo de consulta la ejecuto directamente
        # Ejemplo
        # python manage.py -sql "update channel set channel_name = 'toycantando_edit' where channel_id = 'UC2xjgvWb9cx5F637XjsUNxw'"
        # python manage.py -sql "update channel set channel_name = 'toycantando' where channel_id = 'UC2xjgvWb9cx5F637XjsUNxw'"
        else:
            db.exec(query)