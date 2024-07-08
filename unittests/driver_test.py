import unittest
from unittest.mock import patch, MagicMock

try:
    from src.driver import Driver
except:
    from driver import Driver

class TestDriver(unittest.TestCase):
    
    def setUp(self):
        # Configura cualquier inicialización necesaria antes de cada prueba
        self.mock_driver = MagicMock()

    @patch('driver.webdriver')
    def test_set_driver_chrome(self, mock_webdriver):
        # Configuramos el mock de webdriver.Chrome para el caso de Chrome
        mock_chrome = MagicMock()
        mock_webdriver.Chrome = mock_chrome

        # Creamos una instancia de Driver con 'chrome'
        with Driver(browser="chrome") as driver:
            self.assertEqual(driver.driver, mock_chrome.return_value)
            mock_chrome.assert_called_once()

    @patch('driver.webdriver')
    def test_set_driver_firefox(self, mock_webdriver):
        # Configuramos el mock de webdriver.Firefox para el caso de Firefox
        mock_firefox = MagicMock()
        mock_webdriver.Firefox = mock_firefox

        # Creamos una instancia de Driver con 'firefox'
        with Driver(browser="firefox") as driver:
            self.assertEqual(driver.driver, mock_firefox.return_value)
            mock_firefox.assert_called_once()

    @patch('driver.webdriver')
    def test_set_driver_edge(self, mock_webdriver):
        # Configuramos el mock de webdriver.Edge para el caso de Edge
        mock_edge = MagicMock()
        mock_webdriver.Edge = mock_edge

        # Creamos una instancia de Driver con 'edge'
        with Driver(browser="edge") as driver:
            self.assertEqual(driver.driver, mock_edge.return_value)
            mock_edge.assert_called_once()

    def test_set_driver_invalid_browser(self):
        # Creamos una instancia de Driver con un navegador inválido
        with self.assertRaises(ValueError):
            with Driver(browser="invalid_browser"):
                pass

if __name__ == '__main__':
    unittest.main()
