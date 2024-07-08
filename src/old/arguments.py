import argparse

try:
    from src.youtube_scrap import handle_video_args
    from src.youtube_scrap import handle_channel_args
    from src.test import handle_test_args
    from src.similarweb_scrap import handle_similarweb_args
    from src.sql import handle_sql_args
    from src.db import handle_export_args
    from src.db_fetch import handle_fetch_args
    from src.db_fetch import handle_backup_args
    from src.product_scrap import handle_toys_args
except:
    from youtube_scrap import handle_video_args
    from youtube_scrap import handle_channel_args
    from test import handle_test_args
    from similarweb_scrap import handle_similarweb_args
    from sql import handle_sql_args
    from db import handle_export_args
    from db_fetch import handle_fetch_args
    from db_fetch import handle_backup_args
    from product_scrap import handle_toys_args

def get_parser_args():
    """Crear el parser general"""
    parser = argparse.ArgumentParser()

    # Modulo general
    subparsers = parser.add_subparsers(title='Modulo general', dest='module')

    # Modulos
    scrap_parser = subparsers.add_parser('scrap', help='Modulo principal')
    test_parser = subparsers.add_parser('test', help='Modulo de pruebas')
    video_parser = subparsers.add_parser('video', help='Modulo de scrap de video')
    channel_parser = subparsers.add_parser('channel', help='Modulo de scrao de canal')
    sw_parser = subparsers.add_parser('sw', help='Modulo de scrap de SimilarWebs')
    sql_parser = subparsers.add_parser('sql', help='Modulo de comandos SQL')
    toys_parser = subparsers.add_parser('toys', help='Modulo de comandos SQL')
    news_parser = subparsers.add_parser('news', help='Modulo de noticias')
    backup_parser = subparsers.add_parser('backup', help='Modulo de generacion de backups')
    export_parser = subparsers.add_parser('export', help='Modulo de exportacion de la base de datos')
    fetch_parser = subparsers.add_parser('fetch', help='Modulo de analisis de sanidad')

    # Modulo general
    scrap_parser.add_argument('-ay', '--ayuda', action='store_true', help='Mensaje de ayuda')
    scrap_parser.add_argument('-all', '--all', action='store_true', help='Scrapear todo')
    scrap_parser.add_argument('-yt', '--youtube', action='store_true', help='Scrapear YouTube')
    scrap_parser.add_argument('-nw', '--news', action='store_true', help='Scrapear noticias')
    scrap_parser.add_argument('-sw', '--similarweb', action='store_true', help='Scrapear SimilarWebs')
    scrap_parser.add_argument('-toys', '--toys', action='store_true', help='Scrapear juguetes')
    scrap_parser.add_argument('-mail', '--send-mail', action='store_true', help='Scrapear SimilarWebs')
    scrap_parser.add_argument('-to', '--mail_dest', type=str, help='Destinatario del correo')

    # Modulo de tests
    test_parser.add_argument('-ay', '--ayuda', action='store_true', help='Mensaje de ayuda')
    test_parser.add_argument('-l', '--list', nargs='?', const='all', default=None, help='Listar tests')
    test_parser.add_argument('-r', '--run', metavar='RUN_LIST', dest='test_list', type=int, nargs='*', help='Correr un lista de tests')

    # Modulo de videos
    video_parser.add_argument('-ay', '--ayuda', action='store_true', help='Mensaje de ayuda')
    video_parser.add_argument('-i', '--id', type=str, help='ID del video')
    video_parser.add_argument('-u', '--url', type=str, help='URL del video')
    video_parser.add_argument('-add', '--add', action='store_true', help='Agregar un video a la base de datos')
    video_parser.add_argument('-del', '--delete', type=str, help='Borrar un video de la base de datos')
    video_parser.add_argument('-save-html', '--save-html', action='store_true', help='Guardar contenido HTML del video')

    # Modulo de canales
    channel_parser.add_argument('-ay', '--ayuda', action='store_true', help='Mensaje de ayuda')
    channel_parser.add_argument('-i', '--id', type=str, help='ID del canal')
    channel_parser.add_argument('-u', '--url', type=str, help='URL del canal')
    channel_parser.add_argument('-add', '--add', type=str, help='Agregar un canal a la base de datos')
    channel_parser.add_argument('-del', '--delete', type=str, help='Borrar un canal de la base de datos')
    channel_parser.add_argument('-save-html', '--save-html', action='store_true', help='Guardar contenido HTML del canal')

    # Modulo de SimilarWebs
    sw_parser.add_argument('-ay', '--ayuda', action='store_true', help='Mensaje de ayuda')
    sw_parser.add_argument('-add', '--add', type=str, help='Agregar una web usando un dominio URL')
    sw_parser.add_argument('-del', '--delete', type=str, nargs=2, help='Borrar un dominio desde la base de datos')
    sw_parser.add_argument('-web', '--web', type=str, help='Scrapear una web')
    sw_parser.add_argument('-o', '--obtain', action='store_true', help='Obtengo la informacion de las web que ya scrapie antes')

    # Modulo de comandos SQL
    sql_parser.add_argument('-ay', '--ayuda', action='store_true', help='Mensaje de ayuda')
    sql_parser.add_argument('-f', '--file', type=str, help='Ejecutar una consulta SQL leida desde un script')
    sql_parser.add_argument('-q', '--query', type=str, help='Ejecutar una consulta SQL obtenida desde teclado')
    sql_parser.add_argument('-get', '--get', metavar=('{VIDEO/CHANNEL}','{ID/NAME}','TARGET'), type=str, nargs=3, help='Ejecutar un comando SELECT en la base de datos')
    sql_parser.add_argument('-sel', '--select', metavar=('{VIDEO/CHANNEL}','{ID/NAME}','TARGET'), type=str, nargs=3, help='Ejecutar un comando SELECT en la base de datos')
    sql_parser.add_argument('-del', '--delete', metavar=('{VIDEO/CHANNEL}','{ID/NAME}','TARGET'), type=str, nargs=3, help='Ejecutar un comando DELETE en la base de datos')

    # Modulo de juguetes
    toys_parser.add_argument('-ay', '--ayuda', action='store_true', help='Mensaje de ayuda')
    toys_parser.add_argument('-all', '--all', action='store_true', help='Hacer un scrap de todas las plataformas')
    toys_parser.add_argument('-am', '--amazon', action='store_true', help='Hacer un scrap de Amazon')
    toys_parser.add_argument('-ml', '--mercadolibre', action='store_true', help='Hacer un scrap de Mercado Libre')

    # Modulo de exportacion de la base de datos
    export_parser.add_argument('-ay', '--ayuda', action='store_true', help='Mensaje de ayuda')
    export_parser.add_argument('-csv', '--tocsv', action='store_true', help='Exporto la base de datos a formato .csv')
    export_parser.add_argument('-xlsx', '--toexcel', action='store_true', help='Exporto la base de datos a formato Excel')
    export_parser.add_argument('-clean_db', '--clean_db', action='store_true', help='Exporto la base de datos limpia')
    export_parser.add_argument('-clean', '--clean', action='store_true', help='Exporto la base de datos limpia')
    export_parser.add_argument('-plots', '--plots', action='store_true', help='Hago los plots usando la capa correspondiente')

    # Modulo de analisis de sanidad
    fetch_parser.add_argument('-ay', '--ayuda', action='store_true', help='Mensaje de ayuda')
    fetch_parser.add_argument('-all', '--all', action='store_true', help='Hacer un fetch de todo')
    fetch_parser.add_argument('-yt', '--youtube', action='store_true', help='Hacer un fetch de Youtube')

    # Modulo de backups
    backup_parser.add_argument('-ay', '--ayuda', action='store_true', help='Mensaje de ayuda')
    backup_parser.add_argument('-all', '--all', action='store_true', help='Hacer un backup de todo')
    backup_parser.add_argument('-db', '--database', action='store_true', help='Hacer un backup de todo')
    backup_parser.add_argument('-restore', '--restore', type=str, help='Restaura una base de datos')

    # Leo los comandos de teclado
    args = parser.parse_args()

    return parser, args

def process_parser_args(parser, args):
    if args.module == 'test':
        handle_test_args(args=args)
    elif args.module == 'video':
        handle_video_args(args=args)
    elif args.module == 'channel':
        handle_channel_args(args=args)
    elif args.module == 'sw':
        handle_similarweb_args(args=args)
    elif args.module == 'sql':
        handle_sql_args(args=args)
    elif args.module == 'toys':
        handle_toys_args(args=args)
    elif args.module == 'news':
        pass
    elif args.module == 'export':
        handle_export_args(args=args)
    elif args.module == 'backup':
        handle_backup_args(args=args)
    elif args.module == 'fetch':
        handle_fetch_args(args=args)
    else:
        parser.print_help()

if __name__ == '__main__':
    parser, args = get_parser_args()
    process_parser_args(parser, args)