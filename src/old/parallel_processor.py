from multiprocessing import Pool
import os
import time
from functools import partial

try:
    from src.logger import Logger
except:
    from src.logger.logger import Logger

# Crear un logger
logger = Logger().get_logger()

def safe_func(inputs):
    """
    Ejecuta una función de manera segura y captura excepciones.

    Esta función toma una tupla que contiene una función y un argumento,
    ejecuta la función con el argumento dado y maneja cualquier excepción
    que pueda ocurrir. Si se produce una excepción, devuelve una tupla con
    el argumento y la excepción. De lo contrario, devuelve el resultado de
    la función.

    :param inputs: Una tupla (func, task) donde 'func' es la función a ejecutar
                y 'task' es el argumento para la función.
    :return: El resultado de la función 'func(task)' si no hay excepciones.
            Si se produce una excepción, devuelve una tupla (task, Exception).
    """
    func, args, kwargs = inputs
    try:
        # Intenta ejecutar la función con el argumento proporcionado
        # Si task es None, ejecuta func() en lugar de func(task)
        # if args is None:
        #     return func()
        # else:
        return func(*args, **kwargs)
    except Exception as e:
        # Si ocurre una excepción, devuelve el argumento y la excepción
        return (args, kwargs), e

class ParallelProcessor:
    ############################################################################
    # Atributos globables
    ############################################################################
    # Atributo de clase para almacenar la instancia única
    _instance = None

    # Configuraciones por defecto
    ORDERED_RESULTS = True
    DEBUG = False

    ############################################################################
    # Metodos de incializacion
    ############################################################################
    # Cuando solicito crear una instancia me aseguro que
    # si ya hay una creada, devuelvo esa misma
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def reset(cls):
        logger.info(f'Reset del ejecutor en paralelo.')
        if cls._instance is not None:
            cls._instance = None
            cls._instance.__init__()

    def __init__(self, num_workers=None, timeout=10):
        """
        Inicializa la clase ParallelProcessor.

        :param num_workers: Número de trabajadores en el pool. Si es None, usa el número de CPUs disponibles.
        :param ordered_results: Booleano para especificar si se requieren resultados en orden.
        :param timeout: Tiempo máximo para esperar los resultados de cada tarea en segundos.
        """
        # Evitar la inicialización múltiple
        # verificando si existe el atributo initialized en la clase
        if not hasattr(self, 'initialized'):
            self.num_workers = num_workers or os.cpu_count()
            self.timeout = timeout
            
            # Marca la instancia como inicializada
            self._initialized = True

    ############################################################################
    # Metodos de ejecucion
    ############################################################################
    def format_args(self, *args, **kwargs):
        """
        Formatea los argumentos posicionales y con nombre en una lista de tuplas (args, kwargs).

        :param args: Argumentos posicionales.
        :param kwargs: Argumentos con nombre.
        :return: Una lista de tuplas (args, kwargs).
        """
        # Obtener el número total de argumentos posicionales
        num_pos_args = len(args)

        # Crear la lista de tuplas (args, kwargs)
        args_list = []
        for i in range(num_pos_args):
            current_args = args[i] if isinstance(args[i], (list, tuple)) else (args[i],)
            current_kwargs = kwargs.get(i, {})
            args_list.append((current_args, current_kwargs))

        return args_list
    
    def execute(self, func, *args, **kwargs):
        """
        Ejecuta una función en paralelo usando un pool de procesos.

        Si self.ORDERED_RESULTS es True, ejecuta las tareas en orden.
        Si es False, ejecuta las tareas sin orden específico.

        :param func: La función a ejecutar.
        :param args: Una lista de argumentos para pasar a la función. Cada elemento de la lista se pasará a una instancia separada de la función en paralelo.
        :return: Una lista de resultados, uno por cada tarea.
        """
        start_time = time.time()
        
        if self.ORDERED_RESULTS is True:
            results = self.execute_ordered(func, *args, **kwargs)
        else:
            results = self.execute_unordered(func, *args, **kwargs)
        
        end_time = time.time()
        execution_time = round( end_time - start_time, 3)
        
        if self.ORDERED_RESULTS is True:
            logger.info(f'Se obtuvieron los resultados para la funcion [{func.__name__}] ordenados en {execution_time} segundos.')
        else:
            logger.info(f'Se obtuvieron los resultados para la funcion [{func.__name__}] desordenados en {execution_time} segundos.')
        
        return results

    def execute_unordered(self, func, args_list=None):
        """
        Ejecuta una función en paralelo sin mantener el orden de los resultados.

        Utiliza un pool de procesos para ejecutar la función con cada argumento
        proporcionado en paralelo y captura cualquier excepción que pueda ocurrir.

        :param func: La función a ejecutar.
        :param args: Una lista de argumentos para pasar a la función.
        :return: Una lista de resultados exitosos, uno por cada tarea.
        """
        try:
            with Pool(processes=self.num_workers) as pool:
                # Utiliza imap_unordered para ejecutar las tareas en paralelo
                if args_list:
                    partial_funcs = [(func, args, kwargs) for args, kwargs in args_list]
                    results = pool.imap_unordered(safe_func, [(pf,) for pf in partial_funcs])
                else:
                    results = pool.imap_unordered(safe_func, [(func, (), {})])

                # Obtengo los resultados de los procesos que terminaron
                successful_results = []
                for result in results:
                    if not isinstance(result, tuple) or not isinstance(result[1], Exception):
                        successful_results.append(result)
                    else:
                        task_arg, error = result
                        if task_arg is None:
                            logger.error(f"Error al intentar ejecutar la tarea [{func.__name__}()].\nError: {error}")
                        else:
                            logger.error(f"Error al intentar ejecutar la tarea [{func.__name__}()] con los argumentos {task_arg}.\nError: {error}")

                return successful_results

        except Exception as e:
            logger.error(f"Error durante la ejecución en paralelo: {e}")
            return None

    def execute_ordered(self, func, args_list=None):
        """
        Ejecuta una función en paralelo manteniendo el orden de los resultados.

        Utiliza un pool de procesos para ejecutar la función con cada argumento
        proporcionado en paralelo, manteniendo el orden de los resultados y capturando
        cualquier excepción que pueda ocurrir.

        :param func: La función a ejecutar.
        :param args: Una lista de argumentos para pasar a la función.
        :return: Una lista de resultados exitosos, uno por cada tarea.
        """
        try:
            with Pool(processes=self.num_workers) as pool:
                results = []
                if args_list:
                    # Aplicar asincrónicamente las tareas al pool
                    # results = [pool.apply_async(safe_func, ((func, task),)) for task in args_list]
                    for args, kwargs in args_list:
                        async_inputs = (func, args, kwargs)
                        async_tuple  = (async_inputs,)
                        async_result = pool.apply_async(safe_func, async_tuple)
                        results.append( async_result )
                else:
                    # Si no hay tasks, simplemente ejecuta func() sin argumentos
                    #results.append( pool.apply_async(safe_func, ((func, None),)) )
                    async_inputs = (func, (), {})
                    async_tuple  = (async_inputs,)
                    async_result = pool.apply_async(safe_func, async_tuple)
                    results.append( async_result )

                # Obtener los resultados a medida que están listos
                pool.close()
                # Esperar a que todas las tareas se completen
                pool.join()

                # Obtengo los resultados de los procesos que terminaron
                successful_results = []
                for result in results:
                    try:
                        # Obtener el resultado o lanzar excepción si tarda demasiado
                        final_result = result.get(timeout=self.timeout)
                        
                        # Filtro los resultados que se obtuvieron sin fallas
                        if not isinstance(final_result, tuple) or not isinstance(final_result[1], Exception):
                            successful_results.append( final_result )
                        else:
                            # Para los casos fallidos intento mostrar informacion
                            # sobre cual fue el problema
                            task_arg, error = final_result
                            if task_arg is None:
                                logger.error(f"Error al intentar ejecutar la tarea [{func.__name__}()].\nError: {error}")
                            else:
                                logger.error(f"Error al intentar ejecutar la tarea [{func.__name__}()] con los argumentos {task_arg}.\nError: {error}")
                                
                    except Exception as e:
                        logger.error(f"Error al obtener los resultados para la funcion [{func.__name__}()].\nError: {e}")
                        
            # Devuelvo los resultados exitosos
            return successful_results
        
        except Exception as e:
            logger.error(f"Error durante la ejecución en paralelo: {e}")
            return None

################################################################################
# Tests
################################################################################
def square(x):
    if x == 3:  # Ejemplo de un error forzado para demostrar la gestión de errores
        raise ValueError("No se puede calcular el cuadrado de 3")
    return x * x

def random_msg():
    return f"Random"

if __name__ == "__main__":
    args = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

    processor = ParallelProcessor(num_workers=4)
    
    results = processor.execute(square, args)
    if results is not None:
        logger.info(f"Resultados: {results}")
    else:
        logger.error("La ejecución en paralelo falló.")
        
    results = processor.execute(random_msg)
    if results is not None:
        logger.info(f"Resultados: {results}")
    else:
        logger.error("La ejecución en paralelo falló.")
