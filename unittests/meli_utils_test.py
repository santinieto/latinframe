import unittest
from unittest.mock import patch, Mock

try:
    from src.meli_utils import MeLiProductListings
    from src.utils import get_http_response
except:
    from meli_utils import MeLiProductListings
    from utils import get_http_response

class TestMeLiProductListings(unittest.TestCase):
    def test_singleton_instance(self):
        # Ensure only one instance is created
        listings1 = MeLiProductListings(['computadoras', 'celulares'])
        listings2 = MeLiProductListings(['televisores', 'audífonos'])
        
        self.assertIs(listings1, listings2)
        
        # Borro el objeto
        del listings1
        del listings2

    @patch('requests.get')
    def test_fetch_html_content_success(self, mock_get_http_response):
        # Simula una respuesta exitosa
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = '<html><body>Contenido HTML</body></html>'
        mock_response.text = mock_response.content
        mock_get_http_response.return_value = mock_response

        # Crea una instancia de MeLiProductListings
        listings = MeLiProductListings(['computadoras', 'celulares'])
        listings.generate_urls()

        # Llama al método fetch_html_content
        listings.fetch_html_content()

        # Asegura que listings contenga el contenido HTML esperado
        for topic in listings.topics:
            self.assertIn(topic, listings.listings)
            self.assertIn('html_content', listings.listings[topic])
            self.assertEqual(str(listings.listings[topic]['html_content']), mock_response.content)
        
        # Borro el objeto
        del listings

    @patch('requests.get')
    def test_fetch_html_content_failure(self, mock_get_http_response):
        # Simula una respuesta fallida
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 404
        mock_response.content = 'Error'
        mock_response.text = mock_response.content
        mock_get_http_response.return_value = mock_response

        # Crea una instancia de MeLiProductListings
        listings = MeLiProductListings(['computadoras', 'celulares'])
        listings.generate_urls()

        # Llama al método fetch_html_content
        listings.fetch_html_content()

        # Asegura que se registre un mensaje de error para cada tema
        for topic in listings.topics:
            self.assertIn(topic, listings.listings)
            self.assertIn('Error', listings.listings[topic]['html_content'])
        
        # Borro el objeto
        del listings

if __name__ == '__main__':
    unittest.main()