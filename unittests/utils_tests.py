# Imports estándar de Python
import os
import sys
import io

# Añade la ruta del directorio principal al sys.path
current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path, '..'))  # Ajusta según la estructura de tu proyecto
sys.path.append(project_root)

# Imports de terceros
import unittest
from unittest.mock import patch, Mock

# Imports locales
from src.utils.utils import *
from src.logger.logger import Logger

################################################################################
# Genero una instancia del Logger
################################################################################
logger = Logger(os.path.basename(__file__)).get_logger()

class TestUtils(unittest.TestCase):

    @patch('requests.get')
    def test_get_http_response_page(self, mock_get):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.content = '<html><head><title>Test</title></head><body>Content</body></html>'.encode('utf-8')
        mock_get.return_value = mock_response

        url = 'http://example.com'
        response = get_http_response(url)
        self.assertIsInstance(response, BeautifulSoup)
        self.assertEqual(response.title.string, 'Test')

    @patch('requests.get')
    def test_get_http_response_text(self, mock_get):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.text = 'Some plain text content'
        mock_response.content = mock_response.text.encode('utf-8')
        mock_get.return_value = mock_response

        url = 'http://example.com'
        response = get_http_response(url, response_type='text')
        self.assertIsInstance(response, str)
        self.assertEqual(response, 'Some plain text content')

    @patch('requests.get')
    def test_get_http_response_invalid_url(self, mock_get):
        with self.assertRaises(ValueError):
            get_http_response(1234)

    @patch('requests.get')
    def test_get_http_response_invalid_headers(self, mock_get):
        with self.assertRaises(ValueError):
            get_http_response('http://example.com', headers='invalid_headers')

    @patch('requests.get')
    def test_get_http_response_invalid_response_type(self, mock_get):
        with self.assertRaises(ValueError):
            get_http_response('http://example.com', response_type='invalid')

    @patch('requests.get')
    def test_get_http_response_timeout(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout
        response = get_http_response('http://example.com', timeout=0.001)
        self.assertIsNone(response)

    @patch('requests.get')
    def test_get_http_response_404(self, mock_get):
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_response.content = 'Not Found'.encode('utf-8')
        mock_get.return_value = mock_response

        url = 'http://example.com'
        response = get_http_response(url)
        self.assertIsNone(response)

    @patch('requests.get')
    def test_retry_attempts(self, mock_get):
        # Mock successful response for first 2 attempts, successful response on 3rd attempt
        mock_failed_response = Mock()
        mock_failed_response.ok = False
        mock_failed_response.status_code = 404
        mock_failed_response.content = b'Not Found'

        mock_successful_response = Mock()
        mock_successful_response.ok = True
        mock_successful_response.status_code = 200
        mock_successful_response.content = b'<html><body><h1>Hello, World!</h1></body></html>'

        mock_get.side_effect = [mock_failed_response, mock_failed_response, mock_successful_response]

        # Call the function with retry_attempts=3
        url = 'https://example.com'
        response = get_http_response(url, retry_attempts=3)

        # Assert that response is correct
        self.assertEqual(response, None)

    @patch('platform.system')
    def test_get_os_windows(self, mock_system):
        mock_system.return_value = 'Windows'
        self.assertEqual(get_os(), 'Windows')

    @patch('platform.system')
    def test_get_os_linux(self, mock_system):
        mock_system.return_value = 'Linux'
        self.assertEqual(get_os(), 'Linux')

    @patch('platform.system')
    def test_get_os_mac(self, mock_system):
        mock_system.return_value = 'Darwin'
        self.assertEqual(get_os(), 'Darwin')

    @patch('platform.system')
    def test_get_os_empty_string(self, mock_system):
        mock_system.return_value = ''
        with self.assertRaises(RuntimeError) as context:
            get_os()
        self.assertIn("No se pudo determinar el sistema operativo", str(context.exception))

    @patch('platform.system')
    def test_get_os_exception(self, mock_system):
        mock_system.side_effect = Exception('Simulated Exception')
        with self.assertRaises(RuntimeError) as context:
            get_os()
        self.assertIn("Error al obtener el sistema operativo: Simulated Exception", str(context.exception))


    def test_clean_and_parse_number_simple(self):
        self.assertEqual(clean_and_parse_number("123"), 123.0)

    def test_clean_and_parse_number_with_commas(self):
        self.assertEqual(clean_and_parse_number("1,234"), 1234.0)

    def test_clean_and_parse_number_with_units_k(self):
        self.assertEqual(clean_and_parse_number("1.5k"), 1500.0)
        self.assertEqual(clean_and_parse_number("1.5K"), 1500.0)

    def test_clean_and_parse_number_with_units_m(self):
        self.assertEqual(clean_and_parse_number("2M"), 2000000.0)
        self.assertEqual(clean_and_parse_number("2m"), 0.002)

    def test_clean_and_parse_number_with_complex_text(self):
        self.assertEqual(clean_and_parse_number("'230"), 230.0)
        self.assertEqual(clean_and_parse_number("'230 k"), 230000.0)
        self.assertEqual(clean_and_parse_number("'230 M"), 230000000.0)
        self.assertEqual(clean_and_parse_number("'230 T"), 230000000000000.0)
        self.assertEqual(clean_and_parse_number("'230k"), 230000.0)
        self.assertEqual(clean_and_parse_number("'230M"), 230000000.0)
        self.assertEqual(clean_and_parse_number("'230T"), 230000000000000.0)

    def test_clean_and_parse_number_with_units_g(self):
        self.assertEqual(clean_and_parse_number("3G"), 3000000000.0)

    def test_clean_and_parse_number_with_units_t(self):
        self.assertEqual(clean_and_parse_number("4T"), 4000000000000.0)

    def test_clean_and_parse_number_with_invalid_string(self):
        self.assertEqual(clean_and_parse_number("abc"), 0.0)

    def test_clean_and_parse_number_with_mixed_content(self):
        self.assertEqual(clean_and_parse_number("1.5kabc"), 1500.0)

    def test_clean_and_parse_number_with_invalid_unit(self):
        self.assertEqual(clean_and_parse_number("1.5x"), 1.5)
    
    @patch.dict(os.environ, {"INT_VAR": "123", "FLOAT_VAR": "123.45", "BOOL_VAR": "true", "JSON_VAR": '{"key": "value"}', "STR_VAR": "hello"})
    def test_getenv_int(self):
        self.assertEqual(getenv("INT_VAR", 0), 123)
    
    @patch.dict(os.environ, {"FLOAT_VAR": "123.45"})
    def test_getenv_float(self):
        self.assertEqual(getenv("FLOAT_VAR", 0.0), 123.45)
    
    @patch.dict(os.environ, {"BOOL_VAR": "true"})
    def test_getenv_bool(self):
        self.assertEqual(getenv("BOOL_VAR", False), True)
    
    @patch.dict(os.environ, {"JSON_VAR": '{"key": "value"}'})
    def test_getenv_json(self):
        self.assertEqual(getenv("JSON_VAR", {}), {"key": "value"})
    
    @patch.dict(os.environ, {"STR_VAR": "hello"})
    def test_getenv_str(self):
        self.assertEqual(getenv("STR_VAR", "default"), "hello")
    
    @patch.dict(os.environ, {})
    def test_getenv_default(self):
        self.assertEqual(getenv("NON_EXISTENT_VAR", "default"), "default")
    
    @patch.dict(os.environ, {"MIXED_VAR": "123"})
    def test_getenv_mixed(self):
        self.assertEqual(getenv("MIXED_VAR", "default"), 123)
    
    @patch.dict(os.environ, {"INVALID_BOOL_VAR": "not_a_bool"})
    def test_getenv_invalid_bool(self):
        self.assertEqual(getenv("INVALID_BOOL_VAR", "default"), "not_a_bool")
    
    @patch.dict(os.environ, {"INVALID_JSON_VAR": "not_a_json"})
    def test_getenv_invalid_json(self):
        self.assertEqual(getenv("INVALID_JSON_VAR", "default"), "not_a_json")

    def test_generate_random_user_agent_valid_type(self):
        # Caso de prueba: tipo de User Agent válido (Chrome)
        user_agent = generate_random_user_agent(0)
        self.assertTrue(user_agent.startswith("Mozilla/5.0"))
        self.assertTrue("Chrome" in user_agent)

    def test_generate_random_user_agent_random_type(self):
        # Caso de prueba: no se proporciona ningún tipo de User Agent
        user_agent = generate_random_user_agent()
        self.assertTrue(user_agent.startswith("Mozilla/5.0"))

    def test_generate_random_user_agent_invalid_type(self):
        # Caso de prueba: tipo de User Agent no válido
        with self.assertRaises(ValueError):
            generate_random_user_agent(5)

    def test_get_time_len_seconds_to_hours_str(self):
        # Caso de prueba: convertir 3600 segundos a horas en formato de cadena
        self.assertEqual(get_time_len(3600, unit="hours", input_format="seconds", output_format="str"), "01:00:00")

    def test_get_time_len_minutes_to_seconds_float(self):
        # Caso de prueba: convertir 30 minutos a segundos en formato de punto flotante
        self.assertEqual(get_time_len(30, unit="seconds", input_format="minutes", output_format="float"), 1800.0)

    def test_get_time_len_invalid_input(self):
        # Caso de prueba: pasar una cadena no numérica como tiempo
        self.assertEqual(get_time_len("abc", unit="hours", input_format="seconds", output_format="str"), 0)

    def test_get_time_len_invalid_unit(self):
        # Caso de prueba: pasar una unidad de tiempo no válida
        self.assertEqual(get_time_len(3600, unit="weeks", input_format="seconds", output_format="str"), 0)

    def test_get_time_len_negative_time(self):
        # Caso de prueba: pasar un tiempo negativo
        self.assertEqual(get_time_len(-3600, unit="hours", input_format="seconds", output_format="str"), 0)

    def test_get_formatted_date_valid_format(self):
        # Caso de prueba con un formato válido
        formatted_date = get_formatted_date("%Y%m%d_%H%M%S")
        self.assertIsNotNone(formatted_date)
        # Verificar que la fecha y hora están formateadas correctamente
        self.assertRegex(formatted_date, r"\d{8}_\d{6}")

    def test_get_date_from_filename_valid(self):
        # Caso de prueba con un nombre de archivo válido y el patrón de fecha correcto
        filename = "archivo_20220530_120000.txt"
        self.assertEqual(get_date_from_filename(filename), ('20220530', '120000'))

    def test_get_date_from_filename_invalid_format(self):
        # Caso de prueba con un nombre de archivo en un formato que no coincide con el patrón de fecha especificado
        filename = "archivo_20220530_12.txt"
        self.assertEqual(get_date_from_filename(filename), ('00000000', '000000'))

    def test_get_date_from_filename_invalid_date(self):
        # Caso de prueba con un nombre de archivo con una fecha/hora incorrecta
        filename = "archivo_20220532_250000.txt"
        self.assertEqual(get_date_from_filename(filename), ('00000000', '000000'))

    def test_get_newest_file_valid(self):
        # Caso de prueba con una lista válida de nombres de archivos
        filename_list = [
            "archivo1_20220530_120000.txt",
            "archivo2_20220531_130000.txt",
            "archivo3_20220601_140000.txt"
            ]
        self.assertEqual(get_newest_file(filename_list), "archivo3_20220601_140000.txt")

    def test_get_newest_file_empty_list(self):
        # Caso de prueba con una lista vacía de nombres de archivos
        filename_list = []
        self.assertIsNone(get_newest_file(filename_list))
        
    def test_get_newest_file_invalid_format(self):
        # Caso de prueba con una lista de nombres de archivos en un formato no válido
        filename_list = [
            "arc-2005000ss.txt",
            "archivo2_2022-05-30000.txt",
            "archivo3_20220601140000.txt"
            ]
        self.assertIsNone(get_newest_file(filename_list))

    def test_get_newest_file_various_format(self):
        # Caso de prueba con una lista de nombres de archivos en varios formatos
        filename_list = [
            "archivo1_20220530_120000.txt",
            "archivo2_2022-05-31_130000.txt",
            "archivo3_20220601_140000.txt"
            ]
        self.assertEqual(get_newest_file(filename_list), "archivo3_20220601_140000.txt")

    def test_is_url_arg(self):
        self.assertTrue(is_url_arg('https://example.com'))
        self.assertTrue(is_url_arg('http://example.com'))
        self.assertTrue(is_url_arg('example.com'))
        self.assertTrue(is_url_arg('programme-tv.net'))
        self.assertTrue(is_url_arg('https://sub.example.com/path'))
        self.assertTrue(is_url_arg('http://example.com:8080'))
        self.assertFalse(is_url_arg('not_a_url'))
        self.assertFalse(is_url_arg('ftp://example.com'))
        self.assertFalse(is_url_arg('example'))
        self.assertFalse(is_url_arg('example.'))
        self.assertTrue(is_url_arg('programme-tv.net'))
        self.assertTrue(is_url_arg('http://programme-tv.net'))
        self.assertTrue(is_url_arg('https://programme-tv.net'))
        self.assertTrue(is_url_arg('www.programme-tv.net'))
        self.assertFalse(is_url_arg('not a url'))
        self.assertFalse(is_url_arg('programme-tv'))
        self.assertFalse(is_url_arg('http:/programme-tv.net'))
        self.assertFalse(is_url_arg('https:/programme-tv.net'))

    def test_safe_get_from_json(self):
        data = {
            'a': {
                'b': {
                    'c': 'd'
                },
                'e': 'f'
            }
        }

        # Caso básico de prueba
        self.assertEqual(safe_get_from_json(data, ['a', 'b', 'c']), 'd')
        # Caso de valor por defecto
        self.assertEqual(safe_get_from_json(data, ['a', 'x', 'y'], default='not found'), 'not found')
        # Caso de acceso a valor no diccionario
        self.assertEqual(safe_get_from_json(data, ['a', 'e', 'x'], default='not found'), 'not found')
        # Caso de acceso con lista vacía de claves
        self.assertEqual(safe_get_from_json(data, [], default='default'), data)
        # Caso de valor por defecto None
        self.assertEqual(safe_get_from_json(data, ['a', 'x', 'y']), None)
        # Caso de claves que existen en la ruta
        self.assertEqual(safe_get_from_json(data, ['a', 'e']), 'f')
        # Caso de diccionario no anidado
        self.assertEqual(safe_get_from_json({'key': 'value'}, ['key']), 'value')
        self.assertEqual(safe_get_from_json({'key': 'value'}, ['missing_key'], default='default'), 'default')

    def test_valid_times(self):
        self.assertEqual(fit_time_to_24_hours('25:00:00'), '1:01:00:00')
        self.assertEqual(fit_time_to_24_hours('48:00:00'), '2:00:00:00')
        self.assertEqual(fit_time_to_24_hours('72:00:00'), '3:00:00:00')
        self.assertEqual(fit_time_to_24_hours('1:00:00'), '0:01:00:00')
        self.assertEqual(fit_time_to_24_hours('0:59:59'), '0:00:59:59')
        self.assertEqual(fit_time_to_24_hours('24:00:00'), '1:00:00:00')
        self.assertEqual(time_to_seconds('10:20:30'), 37230)
        self.assertEqual(time_to_seconds('00:00:00'), 0)
        self.assertEqual(time_to_seconds('23:59:59'), 86399)
    
    def test_invalid_format(self):
        self.assertEqual(fit_time_to_24_hours('25:00'), '0:00:00:00')
        self.assertEqual(fit_time_to_24_hours('invalid'), '0:00:00:00')
        self.assertEqual(fit_time_to_24_hours('10:60:00'), '0:00:00:00')
        self.assertEqual(time_to_seconds('10:60:00'), 0)
        self.assertEqual(time_to_seconds('25:30:00'), 0)
        self.assertEqual(time_to_seconds('10:20:70'), 0)
        self.assertEqual(time_to_seconds('abc:def:ghi'), 0)
        self.assertEqual(time_to_seconds('10:20'), 0)
        self.assertEqual(time_to_seconds('10:20:30:40'), 0)
        self.assertEqual(time_to_seconds('12:34:56:78'), 0)

    def test_edge_cases(self):
        self.assertEqual(fit_time_to_24_hours('00:00:00'), '0:00:00:00')
        self.assertEqual(fit_time_to_24_hours('23:59:59'), '0:23:59:59')
        self.assertEqual(fit_time_to_24_hours('24:00:00'), '1:00:00:00')
        self.assertEqual(fit_time_to_24_hours('1000:00:00'), '41:16:00:00')

    def test_valid_iso_duration(self):
        # Test with valid ISO duration
        self.assertEqual(transform_duration_format('PT10H20M30S'), '10:20:30')
        self.assertEqual(transform_duration_format('PT1H0M0S'), '01:00:00')
        self.assertEqual(transform_duration_format('PT0H5M0S'), '00:05:00')
        self.assertEqual(transform_duration_format('PT0H0M30S'), '00:00:30')
        self.assertEqual(transform_duration_format('P2DT12H30M45S'), '60:30:45')

    def test_invalid_iso_duration(self):
        # Test with invalid ISO duration
        self.assertEqual(transform_duration_format('PT'), '00:00:00')
        self.assertEqual(transform_duration_format(''), '00:00:00')
        self.assertEqual(transform_duration_format('PT10H20M'), '10:20:00')
        self.assertEqual(transform_duration_format('PT10H20S'), '10:00:20')
        self.assertEqual(transform_duration_format('PT10H'), '10:00:00')
        self.assertEqual(transform_duration_format('PT20M30S'), '00:20:30')

    def test_valid_domain(self):
        domain = "example.com"
        expected_url = f"{SIMILARWEB_BASE_URL}/website/example.com/#overview"
        url, _ = get_similarweb_url_tuple(domain)
        self.assertEqual(url, expected_url)

    def test_valid_domain_2(self):
        domain = "programme-tv.net"
        expected_url = f"{SIMILARWEB_BASE_URL}/website/programme-tv.net/#overview"
        url, _ = get_similarweb_url_tuple(domain)
        self.assertEqual(url, expected_url)

    def test_invalid_domain(self):
        domain = "invalid_domain"
        url, _ = get_similarweb_url_tuple(domain)
        self.assertIsNone(url)
        
    def test_join_individual_string(self):
        self.assertEqual(join_str("cadena1"), "cadena1")

    def test_join_list_of_strings(self):
        self.assertEqual(join_str(["cadena1", "cadena2", "cadena3"]), "cadena1,cadena2,cadena3")

    def test_join_list_of_strings_with_separator(self):
        self.assertEqual(join_str(["cadena1", "cadena2", "cadena3"], separator=';'), "cadena1;cadena2;cadena3")

    def test_join_empty_list(self):
        self.assertEqual(join_str([]), "")

    def test_join_empty_string(self):
        self.assertEqual(join_str(""), "")

    def test_join_non_string_or_list(self):
        self.assertEqual(join_str(123), "")
        self.assertEqual(join_str({"a": 1, "b": 2}), "")

    def test_join_with_integer_elements(self):
        self.assertEqual(join_str([1, 2, 3]), "1,2,3")

    def test_join_with_float_elements(self):
        self.assertEqual(join_str([1.1, 2.2, 3.3]), "1.1,2.2,3.3")

    def test_join_with_boolean_elements(self):
        self.assertEqual(join_str([True, False]), "True,False")

    def test_join_with_empty_string_elements(self):
        self.assertEqual(join_str(["", "", ""]), ",".join(["", "", ""]))

    def test_join_with_custom_separator(self):
        self.assertEqual(join_str(["a", "b", "c"], separator=';'), "a;b;c")

    def test_join_with_large_list(self):
        elements = [str(i) for i in range(10000)]
        expected_result = ",".join(elements)
        self.assertEqual(join_str(elements), expected_result)

    def test_join_individual_string(self):
        self.assertEqual(join_str("cadena1"), "cadena1")

    def test_join_list_of_strings(self):
        self.assertEqual(join_str(["cadena1", "cadena2", "cadena3"]), "cadena1,cadena2,cadena3")

    def test_join_list_of_strings_with_separator(self):
        self.assertEqual(join_str(["cadena1", "cadena2", "cadena3"], separator=';'), "cadena1;cadena2;cadena3")

    def test_join_empty_list(self):
        self.assertEqual(join_str([]), "")

    def test_join_empty_string(self):
        self.assertEqual(join_str(""), "")

    def test_join_non_string_or_list(self):
        self.assertEqual(join_str(123), "")
        self.assertEqual(join_str({"a": 1, "b": 2}), "")

    def test_database_format_1(self):
        self.assertEqual(join_str("cadena1", format_db=True), 'cadena1')

    def test_database_format_2(self):
        self.assertEqual(join_str(["cadena1"], format_db=True), '"cadena1"')

    def test_database_format_3(self):
        self.assertEqual(join_str(["cadena1", "cadena2", "cadena3"], format_db=True), '"cadena1","cadena2","cadena3"')

    def test_join_normal(self):
        self.assertEqual(join_str(["cadena1", "cadena2", "cadena3"]), 'cadena1,cadena2,cadena3')

    def test_join_with_separator(self):
        self.assertEqual(join_str(["cadena1", "cadena2", "cadena3"], ';'), 'cadena1;cadena2;cadena3')

    def test_none_input(self):
        self.assertEqual(join_str(None), '')

    def test_empty_string(self):
        self.assertEqual(join_str(""), '')

    def test_empty_list(self):
        self.assertEqual(join_str([]), '')

    def test_elements_to_kwargs_with_tuples(self):
        result = elements_to_kwargs(('a', 1), ('b', 2), ('c', 3))
        self.assertEqual(result, {'a': 1, 'b': 2, 'c': 3})

    def test_elements_to_kwargs_with_kwargs(self):
        result = elements_to_kwargs(('x', 'valor_x'), y='valor_y', z='valor_z')
        self.assertEqual(result, {'x': 'valor_x', 'y': 'valor_y', 'z': 'valor_z'})

    def test_elements_to_kwargs_with_mixed_arguments(self):
        result = elements_to_kwargs(('a', 1), ('c', 3), b=2,  d=4)
        self.assertEqual(result, {'a': 1, 'b': 2, 'c': 3, 'd': 4})

    def test_elements_to_kwargs_with_empty_arguments(self):
        result = elements_to_kwargs()
        self.assertEqual(result, {})

    def test_elements_to_kwargs_with_invalid_arguments(self):
        with self.assertRaises(TypeError):
            elements_to_kwargs(('a', 1), ('b',))

    def test_get_param_from_kwargs(self):
        result = get_param(target='parametro', default=10, parametro=20)
        self.assertEqual(result, 20)

    def test_get_param_from_args(self):
        result = get_param('parametro', 10, 1, 30, 'valor_extra')
        self.assertEqual(result, 'valor_extra')

    def test_get_param_default_value(self):
        result = get_param('parametro', 10)
        self.assertEqual(result, 10)

    def test_get_param_no_value(self):
        result = get_param('parametro', 10, 1)  # 'parametro' no está en kwargs ni en args
        self.assertEqual(result, 10)

    def test_get_param_no_default(self):
        result = get_param('parametro')
        self.assertIsNone(result)  # 'parametro' no está en kwargs ni se proporciona un valor predeterminado


if __name__ == "__main__":
    unittest.main()