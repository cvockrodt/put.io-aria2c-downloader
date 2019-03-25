"""Test Config file
"""
import os
import xmlrpc.client

import putiopy

from putio_downloader import PutioAria2cDownloader


def test_config():
    kwargs = {
        'oauth_token': 'XXXXXXXX',
        'keep_folder_structure': True,
        'aria2c_secret_token': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
        'root_watch_dir': 0,
        'watch_folders': ['isos', 'news', 'videos'],
        'rpc_url': 'https://example.com:6800/rpc'
    }

    test_instance = PutioAria2cDownloader(**kwargs)
    assert test_instance.keep_folder_structure
    assert test_instance.aria2c_secret_token == 'token:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
    assert test_instance.root_download_dir.startswith('/tmp/')
    assert test_instance.post_process_dir == os.getcwd()
    assert test_instance.watch_list == ['isos', 'news', 'videos']
    assert not hasattr(test_instance, 'root_watch_dir')
    assert not hasattr(test_instance, 'rpc_url')
    assert isinstance(test_instance.putio_client, putiopy.Client)
    assert isinstance(test_instance.aria_client, xmlrpc.client.ServerProxy)
