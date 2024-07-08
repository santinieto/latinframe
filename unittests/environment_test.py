import os
import json
import unittest
from pathlib import Path

# Asumiendo que las funciones están en un archivo llamado 'environment.py'
from environment import *

class TestEnvironmentFunctions(unittest.TestCase):
    def setUp(self):
        # Crear un archivo JSON temporal para pruebas
        self.credentials_path = Path.cwd() / 'utils' / 'environment_test.json'
        self.credentials_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.credentials_path, 'w') as f:
            json.dump({
                "email": "test@example.com",
                "password": "password123",
                "platform": "example_platform"
            }, f)

    def tearDown(self):
        # Eliminar el archivo JSON temporal después de las pruebas
        if self.credentials_path.exists():
            self.credentials_path.unlink()
        # Limpiar variables de entorno
        for key in [
                "SOFT_HOME", "SOFT_RESULTS", "SOFT_UTILS", "SOFT_LOGS",
                "SOFT_MP_ENABLE", "SOFT_MP_NTHREADS",
                "EMAIL_ADRESS", "EMAIL_PASSWORD", "EMAIL_PLATFORM",
                "email", "password", "platform"
            ]:
            if key in os.environ:
                del os.environ[key]\
    
    def test_unset_environment(self):
        # Testeamos la función unset_environment
        unset_environment(self.credentials_path)

    def test_load_json(self):
        # Testeamos la función load_json
        load_json(filename=str(self.credentials_path))
        self.assertEqual(os.environ.get("email"), "test@example.com")
        self.assertEqual(os.environ.get("password"), "password123")
        self.assertEqual(os.environ.get("platform"), "example_platform")

    def test_set_environment(self):
        # Testeamos la función set_environment
        set_environment(self.credentials_path)

        home = Path.cwd()
        self.assertEqual(os.environ.get("SOFT_HOME"), str(home))
        self.assertEqual(os.environ.get("SOFT_RESULTS"), str(home / 'results'))
        self.assertEqual(os.environ.get("SOFT_UTILS"), str(home / 'utils'))
        self.assertEqual(os.environ.get("SOFT_LOGS"), str(home / 'logs'))
        self.assertEqual(os.environ.get("SOFT_MP_ENABLE"), 'True')
        self.assertEqual(os.environ.get("SOFT_MP_NTHREADS"), str(max(1, os.cpu_count() // 2)))
        self.assertEqual(os.environ.get("EMAIL_ADRESS"), "test@example.com")
        self.assertEqual(os.environ.get("EMAIL_PASSWORD"), "password123")
        self.assertEqual(os.environ.get("EMAIL_PLATFORM"), "example_platform")

    def test_set_environment_missing_file(self):
        # Borro las variables para asegurarme que no existen previamente
        self.test_unset_environment()
        
        # Testeamos la función set_environment cuando falta el archivo de credenciales
        missing_path = Path.cwd() / 'utils' / 'missing_credentials.json'
        load_json(filename=str(missing_path))
        self.assertIsNone(os.environ.get("email"))
        self.assertIsNone(os.environ.get("password"))
        self.assertIsNone(os.environ.get("platform"))

    def test_set_environment_invalid_json(self):
        # Borro las variables para asegurarme que no existen previamente
        self.test_unset_environment()
        
        # Testeamos la función set_environment cuando el archivo JSON es inválido
        invalid_json_path = Path.cwd() / 'utils' / 'invalid_credentials.json'
        with open(invalid_json_path, 'w') as f:
            f.write("{email: test@example.com, password: password123, platform: example_platform}")

        load_json(filename=str(invalid_json_path))
        self.assertIsNone(os.environ.get("email"))
        self.assertIsNone(os.environ.get("password"))
        self.assertIsNone(os.environ.get("platform"))

        # Limpiar archivo inválido después de la prueba
        if invalid_json_path.exists():
            invalid_json_path.unlink()

if __name__ == '__main__':
    unittest.main()
