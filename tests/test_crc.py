"""Test CRC calculation
"""
from putio_downloader import PutioAria2cDownloader


def test_crc():
    config_path = 'config.ini.example'
    test_instance = PutioAria2cDownloader(config=config_path)
    assert test_instance.crc(config_path) == 'ED5B9E9C'
