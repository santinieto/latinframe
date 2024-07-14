import unittest
from unittest.mock import MagicMock, patch
from youtube_api import YoutubeAPI
import os

class TestYoutubeAPI(unittest.TestCase):

    def setUp(self):
        self.api = YoutubeAPI()

    def tearDown(self):
        self.api = None

    def test_initialization_default_config(self):
        # Eliminar las variables de entorno si están cargadas
        os.environ.pop("youtube_api_en", None)
        os.environ.pop("youtube_api_key", None)
        os.environ.pop("youtube_nvideos_fecth", None)
        os.environ.pop("youtube_page_results", None)

        self.api.reset()
        self.assertEqual(self.api.api_key, YoutubeAPI.DEFAULT_API_KEY)
        self.assertEqual(self.api.n_videos_fetch, YoutubeAPI.DEFAULT_N_VIDEOS_FETCH)
        self.assertEqual(self.api.page_results, YoutubeAPI.DEFAULT_PAGE_RESULTS)
        self.assertTrue(self.api.is_enabled())

    def test_initialization_custom_config(self):
        # Establecer las variables de entorno
        custom_youtube_api_en = 'True'
        custom_youtube_api_key = 'YOUR_API_KEY_HERE'
        custom_youtube_nvideos_fecth = 20
        custom_youtube_page_results = 100

        os.environ["youtube_api_en"] = custom_youtube_api_en
        os.environ["youtube_api_key"] = custom_youtube_api_key
        os.environ["youtube_nvideos_fecth"] = str(custom_youtube_nvideos_fecth)
        os.environ["youtube_page_results"] = str(custom_youtube_page_results)

        self.api.reset()
        api = YoutubeAPI(api_key=custom_youtube_api_key)
        self.assertEqual(api.api_key, custom_youtube_api_key)
        self.assertEqual(api.n_videos_fetch, custom_youtube_nvideos_fecth)
        self.assertEqual(api.page_results, custom_youtube_page_results)
        self.assertTrue(api.is_enabled())

    def test_fetch_channel_data_success(self):
        self.api.reset()
        channel_id = 'UC_x5XG1OV2P6uZZ5FSM9Ttw'
        expected_data_keys = [
            'channel_id', 'channel_name', 'custom_url', 'publish_date', 'country',
            'main_playlist', 'channel_views', 'n_videos', 'subscribers', 'daily_subs',
            'monthly_subs', 'video_ids_list', 'subchannels', 'uploads_playlist_id',
            'playlists'
        ]
        channel_data = self.api.fetch_channel_data(channel_id)
        self.assertIsNotNone(channel_data)
        self.assertTrue(all(key in channel_data for key in expected_data_keys))

    @patch('youtube_api.YoutubeAPI.execute')
    def test_fetch_channel_data_failure(self, mock_execute):
        self.api.reset()
        mock_execute.return_value = {'error_code': 404, 'error_message': 'Channel not found', 'quota_exceeded': False}
        channel_id = 'invalid_channel_id'
        channel_data = self.api.fetch_channel_data(channel_id)
        self.assertIsNone(channel_data)

    # Agrega más pruebas según sea necesario para otros métodos y casos de borde

# Creación de un TestSuite para especificar el orden de los tests
def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestYoutubeAPI('test_initialization_default_config'))
    suite.addTest(TestYoutubeAPI('test_initialization_custom_config'))
    suite.addTest(TestYoutubeAPI('test_fetch_channel_data_success'))
    suite.addTest(TestYoutubeAPI('test_fetch_channel_data_failure'))
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())