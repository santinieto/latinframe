import pandas as pd
import numpy as np

from src.database.db_plots import *
from src.utils.utils import fit_time_to_24_hours
from src.utils.utils import time_to_seconds

def has_rows_w_nulls(df):
    """
    Funcion para checkear si una tabla tiene filas
     con valores nulos
    """
    rows_w_nulls = df[df.isnull().any(axis=1)]
    if len(rows_w_nulls) > 0:
        return True
    else:
        return False

def fill_null_values(df, sort_columns=[], method='both'):
    """
    Llena los valores nulos en una columna específica de un DataFrame utilizando un método de llenado hacia adelante o hacia atrás dentro de grupos definidos por columnas de orden.

    Parámetros:
    - df (DataFrame): El DataFrame en el que se realizará el llenado de valores nulos.
    - sort_columns (list, opcional): Una lista de nombres de columnas por las cuales se ordenará el DataFrame antes del llenado.
    - method (str, opcional): El método de llenado a utilizar ('bfill', 'ffill' o 'both').

    Retorna:
    - df (DataFrame): El DataFrame modificado con los valores nulos llenados.

    Ejemplo:
    fill_null_values(df, 'Valor', ['ID', 'Fecha'], method='bfill')
    """
    # Agregar una columna 'INDEX' para mantener los números de fila originales
    df['INDEX'] = df.index

    if sort_columns:
        # Convertir las columnas de orden a tipo datetime si son fechas
        for col in sort_columns:
            if col in df.columns and df[col].dtype == 'datetime64[ns]':
                df[col] = pd.to_datetime(df[col])

        # Ordenar el DataFrame por las columnas de orden
        df = df.sort_values(sort_columns)

    # Llenado hacia adelante o hacia atrás dentro de grupos
    if method == 'bfill':
        df.bfill(inplace=True)
    elif method == 'ffill':
        df.ffill(inplace=True)
    elif method == 'both':
        df.bfill(inplace=True)
        df.ffill(inplace=True)
    else:
        raise ValueError("El método debe ser 'bfill' o 'ffill'.")

    # Ordenar el DataFrame por la columna 'INDEX'
    df = df.sort_values('INDEX')

    # Eliminar la columna 'INDEX' si se desea
    df.drop('INDEX', axis=1, inplace=True)

    return df

def replace_zeros_with_nearest_valid(df, sort_columns, valid_columns, method=2, debug=False):
    """
    Reemplaza los ceros en un DataFrame por el valor válido más cercano en la misma fila.

    Parámetros:
    - df (DataFrame): El DataFrame en el que se realizarán los reemplazos.
    - sort_columns (list): Una lista de nombres de columnas por las cuales se ordenará el DataFrame.
    - valid_columns (list): Una lista de nombres de columnas que se utilizarán para buscar el valor válido más cercano.

    Retorna:
    - df (DataFrame): El DataFrame modificado con los ceros reemplazados.
    """
    # Agregar una columna 'INDEX' para mantener los números de fila originales
    df['INDEX'] = df.index

    if sort_columns:
        # Convertir las columnas de orden a tipo datetime si son fechas
        for col in sort_columns:
            if col in df.columns and df[col].dtype == 'datetime64[ns]':
                df[col] = pd.to_datetime(df[col])

        # Ordenar el DataFrame por las columnas de orden
        # Reinicio los indices porque sino no funciona
        # la utilidad esta
        df = df.sort_values(sort_columns).reset_index()

    # Debug
    if debug is True:
        print(df.head())

    for col in valid_columns:

        # Encuentra la posición de las filas que tienen un valor de 0.0
        zero_indices = df.index[df[col] == 0.0]

        # Metodo 1: Me limito a buscar en los elementos adyacentes
        if method == 1:

            # Itera sobre estas filas y reemplaza el valor de 0.0 por el valor adyacente
            for idx in zero_indices:

                # Debug
                if debug is True:
                    print('{}. {} = {}'.format(idx-1, col, df[col][idx-1]))
                    print('{}. {} = {}'.format(idx,   col, df[col][idx  ]))
                    print('{}. {} = {}'.format(idx+1, col, df[col][idx+1]))

                # Me aseguro que el elemento a reemplazar no sea el primero
                if idx > 0:
                    # Si el valor anterior no es cero, reemplaza por el valor anterior
                    if df.at[idx - 1, col] != 0.0:
                        df.at[idx, col] = df.at[idx - 1, col]
                    # Otra forma que da igual
                    #if df[col][idx-1] != 0.0:
                    #    df[col][idx] = df[col][idx-1]

                # Me aseguro que el elemento a reemplazar no sea el ultimo que tengo
                elif idx < len(df) - 1:
                    # Si el valor siguiente no es cero, reemplaza por el valor siguiente
                    if df.at[idx + 1, col] != 0.0:
                        df.at[idx, col] = df.at[idx + 1, col]
                    # Otra forma que da igual
                    #if df[col][idx+1] != 0.0:
                    #    df[col][idx] = df[col][idx+1]

        # Metodo 2: Busco alrrededor hasta encontrar un elemento no 0
        if method == 2:

            # Itera sobre estas filas y reemplaza el valor de 0.0 por el valor adyacente
            for idx in zero_indices:

                # Debug
                if debug:
                    print('{}. {} = {}'.format(idx-1, col, df[col][idx-1]))
                    print('{}. {} = {}'.format(idx,   col, df[col][idx  ]))
                    print('{}. {} = {}'.format(idx+1, col, df[col][idx+1]))

                # Inicialmente, asumimos que no hay valores válidos adyacentes
                left_idx = None
                right_idx = None

                # Buscamos el valor válido más cercano a la izquierda
                # Supongamos que que estamos en el inidice 50, vamos
                # a buscar en los indices 49, 48, 47, ..., 0
                for i in range(idx - 1, -1, -1):
                    if df.at[i, col] != 0.0:
                        left_idx = i
                        break

                # Buscamos el valor válido más cercano a la derecha
                # Supongamos que que estamos en el inidice 50, vamos
                # a buscar en los indices 51, 51, 53, ..., N-1
                # Donde N es la longitud del DF
                for i in range(idx + 1, len(df)):
                    if df.at[i, col] != 0.0:
                        right_idx = i
                        break

                # Si encontramos valores válidos a ambos lados, tomamos el más cercano
                if left_idx is not None and right_idx is not None:
                    if abs(left_idx - idx) <= abs(right_idx - idx):
                        df.at[idx, col] = df.at[left_idx, col]
                    else:
                        df.at[idx, col] = df.at[right_idx, col]
                elif left_idx is not None:
                    df.at[idx, col] = df.at[left_idx, col]
                elif right_idx is not None:
                    df.at[idx, col] = df.at[right_idx, col]

    # Ordenar el DataFrame por la columna 'INDEX'
    df = df.sort_values('INDEX').reset_index()

    # Eliminar la columna 'INDEX' si se desea
    df.drop('INDEX', axis=1, inplace=True)

    return df

def clean_channel_tables(filename_1, filename_2, save_clean=True):
    # Cargo los CSV
    df_1 = pd.read_csv(filename_1)
    df_2 = pd.read_csv(filename_2)

    # Convertir la columna 'UPDATE_DATE' a objetos de fecha
    # A df_2 en este caso no le hace falta un procesamiento particular
    df_1['UPDATE_DATE'] = pd.to_datetime(df_1['UPDATE_DATE'])

    # Si la tabla tiene campos nulos los limpio
    sort_columns = ['CHANNEL_ID','UPDATE_DATE']
    if has_rows_w_nulls(df=df_1) is True:
        df_1 = fill_null_values(df=df_1, sort_columns=sort_columns)

    # Relleno los posibles valores que sean 0
    # A df_2 en este caso no le hace falta un procesamiento particular
    sort_columns = ['CHANNEL_ID','UPDATE_DATE']
    valid_columns = ['SUBSCRIBERS', 'DAILY_SUBS','MONTHLY_SUBS','TOTAL_VIEWS','VIDEOS_COUNT']
    df_1 = replace_zeros_with_nearest_valid(df=df_1, sort_columns=sort_columns, valid_columns=valid_columns)

    # Borro columnas que se crearon en el proceso
    try:
        df_1.drop('level_0', axis=1, inplace=True)
        df_1.drop('index', axis=1, inplace=True)
    except:
        pass

    # Me quedo con el registro mas nuevo de cada dia
    df_1['UPDATE_DATE_DATE'] = df_1['UPDATE_DATE'].dt.date
    df_1.sort_values(by=['CHANNEL_ID', 'UPDATE_DATE_DATE'], ascending=[True, False], inplace=True)
    df_1 = df_1.drop_duplicates(subset=['CHANNEL_ID', 'UPDATE_DATE_DATE'], keep='first')
    df_1 = df_1.drop(columns=['UPDATE_DATE_DATE'])
    df_1.sort_values(by='RECORD_ID', ascending=True, inplace=True)

    # Guardo los CSV procesados
    if save_clean == True:
        df_1.to_csv( filename_1.replace('.csv','_clean.csv') )
        df_2.to_csv( filename_2.replace('.csv','_clean.csv') )

    return df_1, df_2

def clean_video_tables(filename_1, filename_2, save_clean=True):
    # Cargo los CSV
    df_1 = pd.read_csv(filename_1)
    df_2 = pd.read_csv(filename_2)

    # Convertir la columna 'UPDATE_DATE' a objetos de fecha
    # A df_2 en este caso no le hace falta un procesamiento particular
    df_1['UPDATE_DATE'] = pd.to_datetime(df_1['UPDATE_DATE'])

    # Si la tabla tiene campos nulos los limpio
    sort_columns = ['VIDEO_ID','UPDATE_DATE']
    if has_rows_w_nulls(df=df_1) is True:
        df_1 = fill_null_values(df=df_1, sort_columns=sort_columns)

    # Relleno los posibles valores que sean 0
    # A df_2 en este caso no le hace falta un procesamiento particular
    sort_columns = ['VIDEO_ID','UPDATE_DATE']
    valid_columns = ['VIEWS','LIKES']
    df_1 = replace_zeros_with_nearest_valid(df=df_1, sort_columns=sort_columns, valid_columns=valid_columns)

    # Borro columnas que se crearon en el proceso
    try:
        df_1.drop('level_0', axis=1, inplace=True)
        df_1.drop('index', axis=1, inplace=True)
    except:
        pass

    # En df_2 (lista de videos y sus nombres) voy a borrar los videos que no esten disponibles
    # Crear una máscara booleana basada en las condiciones
    condicion_1 = df_2['PUBLISH_DATE'] == '00/00/00'
    condicion_2 = df_2['VIDEO_NAME'] == 'Unknown'

    # Combinar ambas condiciones usando el operador lógico OR
    mascara = condicion_1 | condicion_2

    # Crear un nuevo DataFrame sin las filas que cumplen con las condiciones
    df_2 = df_2[~mascara]

    # Debug de que los elimine efectivamente
    #print(df_2[ df_2['PUBLISH_DATE'] == '00/00/00' ])
    #print(df_2[ df_2['VIDEO_NAME'] == '00/00/00' ])

    # Si algun video dura mas de 24 horas lo paso a:
    # Dias:Horas:Minutos:Segundos
    # Aplica la función de conversión al DataFrame
    df_2['VIDEO_LEN'] = df_2['VIDEO_LEN'].apply(time_to_seconds)

    # En df_2 saco las filas que tengan VIDEO_ID nulo porque no tengo con
    # con que relacionarlas
    # Eliminar la fila con NaN en la columna "VIDEO_ID"
    df_1 = df_1.dropna(subset=['VIDEO_ID'])
    df_2 = df_2.dropna(subset=['VIDEO_ID'])

    # Armo la lista de IDs disponibles
    valid_ids_1 = df_1['VIDEO_ID'].tolist()
    valid_ids_2 = df_2['VIDEO_ID'].tolist()

    # Elimino las filas que tiene un ID que se corresponde con la otra fila
    df_1 = df_1[df_1['VIDEO_ID'].isin(valid_ids_2)]
    df_2 = df_2[df_2['VIDEO_ID'].isin(valid_ids_1)]

    # Me quedo con el registro mas nuevo de cada dia
    df_1['UPDATE_DATE_DATE'] = df_1['UPDATE_DATE'].dt.date
    df_1.sort_values(by=['VIDEO_ID', 'UPDATE_DATE_DATE'], ascending=[True, False], inplace=True)
    df_1 = df_1.drop_duplicates(subset=['VIDEO_ID', 'UPDATE_DATE_DATE'], keep='first')
    df_1 = df_1.drop(columns=['UPDATE_DATE_DATE'])
    df_1.sort_values(by='RECORD_ID', ascending=True, inplace=True)

    # Paso la duracion de los videos a segundos

    # Guardo los CSV procesados
    if save_clean == True:
        df_1.to_csv( filename_1.replace('.csv','_clean.csv') )
        df_2.to_csv( filename_2.replace('.csv','_clean.csv') )

    return df_1, df_2

def clean_similarweb_tables(filename_1, filename_2, save_clean=True):
    # Cargo los CSV
    df_1 = pd.read_csv(filename_1)
    df_2 = pd.read_csv(filename_2)

    # Convertir la columna 'UPDATE_DATE' a objetos de fecha
    # A df_2 en este caso no le hace falta un procesamiento particular
    df_1['UPDATE_DATE'] = pd.to_datetime(df_1['UPDATE_DATE'])

    # Crear un DataFrame para almacenar las filas con NaN en "DOMAIN"
    rows_to_delete = df_2[df_2['DOMAIN'].isna()]

    # Guardar los valores de "DOMAIN_ID" correspondientes
    domain_id_values = rows_to_delete['DOMAIN_ID'].tolist()

    # Filtrar las filas que NO están en domain_id_values y sobrescribir df_1
    df_1 = df_1[~df_1['DOMAIN_ID'].isin(domain_id_values)]

    # En df_2 saco las filas que tengan DOMAIN nulo porque no tengo con
    # con que relacionarlas
    # Eliminar la fila con NaN en la columna "DOMAIN"
    df_2 = df_2.dropna(subset=['DOMAIN'])

    # Reemplazar los valores nulos en la columna "YEAR_FOUNDER" con 0
    df_2['YEAR_FOUNDER'] = df_2['YEAR_FOUNDER'].fillna(0) 

    # Paso el BOUNCE_RATE a %
    df_1['BOUNCE_RATE'] = df_1['BOUNCE_RATE'].apply(lambda x : x*100.0)

    # Relleno los posibles valores que sean 0
    # A df_2 en este caso no le hace falta un procesamiento particular
    sort_columns = ['DOMAIN_ID','UPDATE_DATE']
    valid_columns = ['GLOBAL_RANK','COUNTRY_RANK', 'CATEGORY_RANK']
    df_1 = replace_zeros_with_nearest_valid(df=df_1, sort_columns=sort_columns, valid_columns=valid_columns)

    # Me quedo con el registro mas nuevo de cada dia
    df_1['UPDATE_DATE_DATE'] = df_1['UPDATE_DATE'].dt.date
    df_1.sort_values(by=['DOMAIN_ID', 'UPDATE_DATE_DATE'], ascending=[True, False], inplace=True)
    df_1 = df_1.drop_duplicates(subset=['DOMAIN_ID', 'UPDATE_DATE_DATE'], keep='first')
    df_1 = df_1.drop(columns=['UPDATE_DATE_DATE'])
    df_1.sort_values(by='RECORD_ID', ascending=True, inplace=True)

    # FIXME: Me faltaria agregar la funcion para pasar 17M a 17000000 que la tengo en otro branch

    # Guardo los CSV procesados
    if save_clean == True:
        df_1.to_csv( filename_1.replace('.csv','_clean.csv') )
        df_2.to_csv( filename_2.replace('.csv','_clean.csv') )

    return df_1, df_2

if __name__ == '__main__':

    # Defino el path de resultados
    CSV_PATH = r'results/db/'

    # # Defino el nombre del archivo
    # FILENAME_1 = r'channel_records.csv'
    # FILENAME_2 = r'channel.csv'

    # # Obtengo los CSV limpios
    # df_1, df_2 = clean_channel_tables(
    #     filename_1 = CSV_PATH + FILENAME_1,
    #     filename_2 = CSV_PATH + FILENAME_2
    # )

    # # Hago los plots de las tablas de canal
    # plot_channel_tables(df_1, df_2)

    # Defino el nombre del archivo
    FILENAME_1 = r'video_records.csv'
    FILENAME_2 = r'video.csv'

    # Obtengo los CSV limpios
    df_1, df_2 = clean_video_tables(
        filename_1 = CSV_PATH + FILENAME_1,
        filename_2 = CSV_PATH + FILENAME_2
    )

    # Defino el nombre del archivo
    FILENAME_1 = r'similarweb_records.csv'
    FILENAME_2 = r'similarweb_domains.csv'

    # # Obtengo los CSV limpios
    # df_1, df_2 = clean_similarweb_tables(
    #     filename_1 = CSV_PATH + FILENAME_1,
    #     filename_2 = CSV_PATH + FILENAME_2
    # )