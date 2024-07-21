import os

def delete_empty_dat_files(directory):
    # Verifica si el directorio existe
    if not os.path.isdir(directory):
        print(f"El directorio {directory} no existe.")
        return

    # Recorre todos los archivos en el directorio
    for filename in os.listdir(directory):
        if filename.endswith(".dat"):
            file_path = os.path.join(directory, filename)
            # Verifica si el archivo está vacío
            if os.path.getsize(file_path) == 0:
                try:
                    os.remove(file_path)
                    print(f"Archivo eliminado: {file_path}")
                except Exception as e:
                    print(f"No se pudo eliminar {file_path}: {e}")

# Cambia 'excluded' por la ruta real de tu carpeta si es necesario
delete_empty_dat_files('./excluded')