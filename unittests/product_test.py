import unittest
from unittest.mock import patch, mock_open
import os

try:
    from src.utils import get_formatted_date
    from src.product import Product
except:
    from utils import get_formatted_date
    from product import Product

class TestProduct(unittest.TestCase):
    
    def setUp(self):
        self.default_values = {
            'product_id': None,
            'name': '',
            'description': '',
            'price': 0.0,
            'cuotas': 1,
            'currency': '',
            'rank': 0,
            'rating': 0.0,
            'rate_count': 0,
            'platform': '',
            'store': '',
            'most_selled': 0,
            'promoted': 0,
            'url': ''
        }
        self.product = Product()
    
    def test_default_initialization(self):
        for key, value in self.default_values.items():
            self.assertEqual(getattr(self.product, key), value)
    
    def test_initialization_with_product_id(self):
        product = Product(product_id=123)
        self.assertEqual(product.product_id, 123)
    
    def test_load_from_dict(self):
        info_dict = {
            'product_id': 123,
            'name': 'Test Product',
            'description': 'This is a test product',
            'price': 19.99,
            'cuotas': 3,
            'currency': 'USD',
            'rank': 1,
            'rating': 4.5,
            'rate_count': 100,
            'platform': 'Amazon',
            'store': 'Test Store',
            'most_selled': 1,
            'promoted': 1,
            'url': 'http://example.com'
        }
        self.product.load_from_dict(info_dict)
        for key, value in info_dict.items():
            self.assertEqual(getattr(self.product, key), value)
    
    def test_to_dicc(self):
        self.product.product_id = 123
        self.product.name = 'Test Product'
        expected_dict = {
            'product_id': 123,
            'name': 'Test Product',
            'description': '',
            'price': 0.0,
            'cuotas': 1,
            'currency': '',
            'rank': 0,
            'rating': 0.0,
            'rate_count': 0,
            'platform': '',
            'store': '',
            'most_selled': 0,
            'promoted': 0,
            'url': ''
        }
        self.assertEqual(self.product.to_dicc(), expected_dict)
    
    def test_set_html(self):
        html_content = '<html><body>Test Content</body></html>'
        self.product.set_html(html_content)
        self.assertEqual(self.product.html_content, html_content)
    
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    @patch.dict(os.environ, {"SOFT_RESULTS": "/fake/path"})
    def test_save_html_content(self, mock_makedirs, mock_open):
        html_content = '<html><body>Test Content</body></html>'
        self.product.product_id = 123
        self.product.set_html(html_content)
        
        self.product.save_html_content()
        
        filename = f'html_product_{self.product.product_id}_{get_formatted_date()}.html'
        filepath = os.path.join("/fake/path", 'products', filename)
        
        mock_makedirs.assert_called_once_with(os.path.join("/fake/path", 'products'), exist_ok=True)
        mock_open.assert_called_once_with(filepath, 'w', encoding='utf-8')
        mock_open().write.assert_called_once_with(html_content)

if __name__ == '__main__':
    unittest.main()
