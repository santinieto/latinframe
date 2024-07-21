# Latinframe Animation Studio

## Descripcion

Latinframe Animation Studio es una aplicación diseñada para facilitar la creación y gestión de proyectos de animación. Con una interfaz gráfica intuitiva y herramientas potentes, permite a los usuarios controlar navegadores web, gestionar bases de datos SQL, y más.
El objetivo de este trabajo consiste en recolectar datos desde diversas fuentes de intenet tales como Youtube, APIs, E-commerces, etc. Los datos son recolectados y almacenados en una base de datos para su posterior tratamiento.

## Requisitos

Es esencial tener Python instalado para poder ejecutar el proyecto. Recomendamos utilizar Anaconda Navigator para una gestión más sencilla de los entornos de desarrollo.
Otro requisito es el de tener una cuenta en Google Developers y contar con una clave para la API de Youtbe. Este paso no es indispensable pero la velocidad del sistema aumenta sustancialmente al utilizar la API mencionada.

## Instalar Python (Anaconda Navigator)

Anaconda Navigator facilita la instalación y gestión de paquetes y entornos de Python. Para instalarlo:

1. Descarga Anaconda Navigator desde el sitio oficial:
2. Descargar Anaconda Navigator (https://www.anaconda.com/products/navigator)

Sigue las instrucciones del instalador para completar la instalación. La instalacion de la herramienta genera varios archivos, los más importantes son "Anaconda Navigator" y "Anaconda Prompt". Para este proyecto se utilizara este último el cual consiste en una consola de comandos con las herramientas necesarias para ejecutar este proyecto.

## Configuracion del entorno (opcional)
Es recomendable crear un entorno virtual para gestionar las dependencias del proyecto. Puedes hacerlo con `venv` o con `conda` si usas Anaconda. La creacion del entorno virtual se recomienda hacerlo desde la carpeta raíz donde se aloja el proyecto.

### Usando venv
```
python -m venv latinframe-env
source latinframe-env/bin/activate  # En macOS/Linux
latinframe-env\Scripts\activate  # En Windows
```

### Usando Anaconda
```
conda create --name latinframe-env python=3.8
conda activate latinframe-env
```

## Instalación de Dependencias

Ahora se pueden instalar las librerias necesarias del proyecto. Podemos instalar todas las dependencias necesarias desde el archivo requirements.txt o podemos instalarlas manualmente:

Lo primero que debemos hacer es actualizar pip:

```
python.exe -m pip install --upgrade pip
pip install --upgrade pip setuptools wheel
```

### Instalar mediante requirements:

```
pip install -r requirements.txt
```

### Instalar manualmente:

```
pip install numpy
pip install python-dateutil
pip install pytz
pip install ninja
pip install requests
pip install beautifulsoup4
pip install cython
pip install pandas
pip install matplotlib
```

## Estructura del proyecto
```
/latinframe
│
├── src/                          # Directorio con el código fuente
│   ├── database/                 #
│   │   ├── db_clean.py           # Utilidades de limpienza sobre la base de datos
│   │   ├── db_fetch.py           # Utilidades de actualizaciones sobre la base de datos
│   │   ├── db_plots.py           # Plots de la base de datos
│   │   └── database.py           # Manejo de base de datos SQL
│   ├── gui/gui.py                # Interfaz gráfica del usuario
│   ├── logger/                   #
│   │   ├── logger_classes.py     # Clases utiles para la interfaz grafica
│   │   └── logger.py             # Clase principal de la GUI
│   ├── menus/                    # Carpeta que contiene los menus de la GUI
│   ├── news/                     #
│   │   ├── google_news.py        # Utilidades para la obtencion de noticias desde Google
│   │   └── new.py                # Clase base de noticia
│   ├── products/                 #
│   │   ├── alibaba_utils.py      # Utilidades para la obtencion de productos desde Alibaba
│   │   ├── ebay_utils.py         # Utilidades para la obtencion de productos desde Ebay
│   │   ├── meli_utils.py         # Utilidades para la obtencion de productos desde Mercado Libre
│   │   ├── product_manager.py    # Gestionador de productos
│   │   └── product.py            # Clase base de producto
│   ├── similarweb/               #
│   │   ├── similarweb_manage.py  # Gestionador de sitios de  SimilarWeb
│   │   └── similarweb.py         # Clase base de sitio web de SimilarWeb
│   ├── utils/                    #
│   │   ├── driver.py             # Clase base para el driver
│   │   ├── environment.py        # Gestion de variables de entorno
│   │   ├── mail.py               # Gestion de envio de correos
│   │   ├── tests.py              #
│   │   └── utils.py              # Funciones utiles del proyecto
│   └── youtube/                  #
│       ├── youtube_api.py        # Clase para controlar la API de Youtube
│       ├── youtube_channel.py    # Clase base de Canal de Youtube
│       ├── youtube_manager.py    # Gestionador de objetos de Youtube
│       ├── youtube_playlist.py   # Clase base de Playlist de Youtube
│       ├── youtube_short.py      # Clase base de Short de Youtube
│       └── youtube_video.py      # Clase base de Video de Youtube
├── drivers/                      # Carpeta que contiene los drivers del proyecto
├── db_backups/                   # Carpeta para resguardos de la base de datos
├── excluded/                     # Carpeta con los archivos de IDs excluidos
├── img/                          # Carpeta para guardar imagenes
├── logs/                         # Carpeta de logs del sistema
├── results/                      # Carpeta donde se guardan los archivos generados por el proyecto
├── utils/                        # Carpeta de utilidades no asociadas directamente con funciones del codigo
├── scripts/                      # Carpeta de scripts utiles
├── unittests/                    # Carpeta de tests unitarios
├── .gitignore                    # Archivo con los ignores de git
├── manage.py                     # Script principal para ejecutar la GUI
├── requirements.txt              # Lista de dependencias del proyecto
├── setup.py                      # Archivo para la compilacion del proyecto
└── README.md                     # Archivo con la documentación del proyecto
```

# Instalacion del proyecto (todavia en Beta)

1. Moverse a la ruta raiz del proyecto

2. Ejecutar el comando

```
python setup.py build
```

3. Esto va a crear un archivo .exe en la carpeta raíz del proyecto el cual debe permanecer en la carpeta donde se creo, si se quiere ejecutar el proyecto desde otro directorio lo recomendable es crear un acceso directo.

NOTA: Al ejecutar el archivo compilado, el multiprocesos se rompe.

## Ejecucion del proyecyo mediante consola

Para iniciar la aplicación, asegúrate de que estás en el directorio latinframe y ejecuta:

```
python manage.py
```

Esto abrira la aplicacion principal del programa la cual permanecerá abierta hasta que el usuario lo disponga.

Dentro de la interfazz se disponen de una serie de opciones (las cuales no están todas implementadas aún) con las cuales el usuario puede operar. Para actualizar todo la base de datos según las configuraciones por defecto se debe presionar el botón indicar en la pantalla principal de la aplicación.

# Configuraciones

En la carpeta utils/settings.json se encuentran las configuraciones del proyecto

# Logs

La salida de la consola queda guardada en la carpeta logs/

# Resultados

Los .html guardados quedan en la carpeta results/