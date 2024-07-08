import unittest

def handle_test_args(args):
    # Defino un nombre por defecto al modulo
    module_name = 'test'

    # Creo el objeto de tipo test
    t = Test(start_dir='./tests/')
    t.get_suite(pattern='test_*.py')
    t.generate_test_list()

    # Muestro el mensaje de ayuda
    if args.ayuda:
        t.help()

    # Listo los tests disponibles con sus respectivos ID
    elif args.list:
        pattern = None if args.list == 'all' else args.list
        t.show_test_list(pattern = pattern)

    # Corro los tests ingresados por el usuario
    elif args.test_list:
        for test in args.test_list:
            t.run(int(test))

    # Mensaje de error por defecto
    else:
        print(f'Modulos {module_name}')
        print(f'\tSe ha producido un error al procesar el comando')
        print(f'\tPuede utilizar {module_name} -h para obtener ayuda')

class Test():
    def __init__(self, start_dir='./tests/'):
        self.start_dir = start_dir
        self.tests = []
        self.commands = []

    def get_suite(self, pattern='test_*.py'):
        self.loader = unittest.TestLoader()
        self.suite = self.loader.discover(start_dir=self.start_dir, pattern=pattern)

    def generate_test_command(self, suite):
        if hasattr(suite, '__iter__'):
            for x in suite:
                self.generate_test_command(x)
        else:
            suite_str = str(suite).split()
            testname = suite_str[0]
            classname = suite_str[1].strip("()")
            cmd = f'{self.start_dir[2:-1]}.{classname}.{testname}'
            self.tests.append((cmd, suite))
            #

    def generate_test_list(self):
        self.generate_test_command(self.suite)

        # Crear una tupla que asocie cada elemento con un número
        self.commands = [(i, elemento[0], elemento[1]) for i, elemento in enumerate(self.tests, 1)]

    def show_test_list(self, pattern=None):
        for test in self.commands:
            if ((pattern is None) or
                (pattern in test[1].lower())
            ):
                print(f'- Test {test[0]} : {test[1]}')

    def run(self, sel):
        runner = unittest.TextTestRunner()
        for test in self.commands:
            if test[0] == sel:
                cmd = f'Command: python -m unittest {test[1]}'
                result = runner.run(test[2])

    def help(self):
        print('Usage:')
        print( '\t -h : Get this help message')
        print( '\t -l : List tests')
        print( '\t\t -"pattern" : Apply a filter to tests (optional)')
        print(f'\t -r : Run a test list (separated with spaces)')