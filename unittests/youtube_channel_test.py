import unittest
import logging
from youtube_channel import YoutubeChannel

class TestYoutubeChannel(unittest.TestCase):
    def setUp(self):
        self.channel_info = {
            'channel_id': 'UC-lHJZR3Gqxm24_Vd_AJ5Yw',
            'channel_name': 'Test Channel',
            'channel_url': 'https://www.youtube.com/c/TestChannel',
            'publish_date': '2022-01-01',
            'country': 'US',
            'main_playlist': 'PL123456',
            'channel_views': 100000,
            'n_videos': 50,
            'subscribers': 5000,
            'daily_subs': 50,
            'monthly_subs': 1000,
            'video_id_list': ['abc123', 'def456'],
            'subchannels': ['Subchannel1', 'Subchannel2'],
            'playlist_id_list': ['Playlist1', 'Playlist2'],
            'short_id_list': ['Short1', 'Short2']
        }

    def test_default_values(self):
        channel = YoutubeChannel()
        default_values = {
            'channel_id': None,
            'channel_name': '',
            'channel_url': '',
            'publish_date': '',
            'country': '',
            'main_playlist': '',
            'channel_views': 0,
            'n_videos': 0,
            'subscribers': 0,
            'daily_subs': 0,
            'monthly_subs': 0,
            'video_id_list': [],
            'subchannels': [],
            'playlist_id_list': [],
            'short_id_list': []
        }
        self.assertEqual(channel.to_dict(), default_values)

    def test_load_from_dict(self):
        channel = YoutubeChannel()
        channel.load_from_dict(self.channel_info)
        self.assertEqual(channel.to_dict(), self.channel_info)

    def test_load_from_dict_missing_id(self):
        channel = YoutubeChannel()
        channel_info_missing_id = self.channel_info.copy()
        del channel_info_missing_id['channel_id']
        with self.assertLogs(level=logging.ERROR):
            channel.load_from_dict(channel_info_missing_id)

    def test_to_dict(self):
        channel = YoutubeChannel(info_dict=self.channel_info)
        self.assertEqual(channel.to_dict(), self.channel_info)

    def test_str(self):
        channel = YoutubeChannel(info_dict=self.channel_info)
        expected_str = (
            f"- ID del canal de YouTube: {self.channel_info['channel_id']}\n"
            f"- Nombre del canal de YouTube: {self.channel_info['channel_name']}\n"
            f"- Vistas del canal de YouTube: {self.channel_info['channel_views']}\n"
            f"- Número de videos del canal de YouTube: {self.channel_info['n_videos']}\n"
            f"- URL personalizada del canal de YouTube: {self.channel_info['channel_url']}\n"
            f"- Lista de reproducción principal del canal de YouTube: {self.channel_info['main_playlist']}\n"
            f"- Fecha de publicación del canal de YouTube: {self.channel_info['publish_date']}\n"
            f"- País del canal de YouTube: {self.channel_info['country']}\n"
            f"- Suscriptores del canal de YouTube: {self.channel_info['subscribers']}\n"
            f"- Suscriptores mensuales del canal de YouTube: {self.channel_info['monthly_subs']}\n"
            f"- Suscriptores diarios del canal de YouTube: {self.channel_info['daily_subs']}\n"
            f"- Lista de IDs de video del canal de YouTube: {self.channel_info['video_id_list']}\n"
            f"- Subcanales del canal de YouTube: {self.channel_info['subchannels']}\n"
            f"- Listas de reproducción del canal de YouTube: {self.channel_info['playlist_id_list']}\n"
            f"- Shorts del canal de YouTube: {self.channel_info['short_id_list']}\n"
        )
        self.assertEqual(str(channel), expected_str)

    def test_add_video_ids_to_list(self):
        # Crear una instancia de TuClase con una cantidad máxima de videos igual a 5
        channel = YoutubeChannel(info_dict=self.channel_info)
        
        # Intento agregar cosas invalidas
        channel.add_video_ids_to_list({"a": 1, "b": 2})
        
        # Agregar algunos IDs de video
        channel.add_video_ids_to_list(["video1", "video2", "video3"])
        
        # Intentar agregar los mismos IDs de video nuevamente, deberían ser ignorados
        channel.add_video_ids_to_list(["video1", "video2", "video3"])
        
        # Agregar más IDs de video hasta alcanzar el límite máximo
        channel.add_video_ids_to_list(["video4", "video5", "video6"])
        channel.add_video_ids_to_list(["video7", "video8", "video9"])
        channel.add_video_ids_to_list(["video10", "video11", "video12"])
        
        # Verificar que la lista de IDs de video sea correcta
        self.assertEqual(
            channel.video_id_list,
            [   "abc123", "def456", "video1",
                "video2", "video3", "video4",
                "video5", "video6", "video7",
                "video8",
            ])

if __name__ == '__main__':
    unittest.main()
