from cx_Freeze import setup, Executable
import os
import shutil
import glob

# Ruta al directorio donde cx_Freeze coloca el ejecutable
build_dir = 'build'

# Ruta al directorio raíz del proyecto
project_root = os.path.dirname(os.path.abspath(__file__))

def move_files():
    # Encuentra el directorio de compilación
    build_subdirs = glob.glob(os.path.join(build_dir, 'exe.*'))
    if build_subdirs:
        exe_dir = build_subdirs[0]  # Usa el primer directorio que coincide
        
        # Archivos y carpetas a mover
        items_to_move = ['lib', 'share', 'manage.exe']
        for item in items_to_move:
            src_path = os.path.join(exe_dir, item)
            dst_path = os.path.join(project_root, item)
            
            if os.path.isdir(src_path):
                if os.path.exists(dst_path):
                    shutil.rmtree(dst_path)  # Elimina la carpeta destino si existe
                shutil.copytree(src_path, dst_path)
                print(f"Carpeta copiada a: {dst_path}")
            elif os.path.isfile(src_path):
                if os.path.exists(dst_path):
                    os.remove(dst_path)  # Elimina el archivo destino si existe
                shutil.copy(src_path, dst_path)
                print(f"Archivo copiado a: {dst_path}")
            else:
                print(f"El archivo o carpeta {src_path} no existe.")
        
        # Mover archivos DLL
        dll_files = glob.glob(os.path.join(exe_dir, '*.dll'))
        for dll in dll_files:
            dst_path = os.path.join(project_root, os.path.basename(dll))
            if os.path.exists(dst_path):
                os.remove(dst_path)  # Elimina el archivo DLL destino si existe
            shutil.copy(dll, dst_path)
            print(f"Archivo DLL copiado a: {dst_path}")
    else:
        print("No se encontró ningún directorio de compilación.")

# Configuración de cx_Freeze
setup(
    name="manage",
    version="1.0",
    description="Mi aplicación GUI",
    executables=[Executable('manage.py', base='Win32GUI')],
    options={
        'build_exe': {
            'packages': ['src'],
            'include_files': [('src', 'src')],
        }
    },
)

# Llama a la función para mover los archivos después de la construcción
move_files()
