"""Put.io Aria2c Downloader
"""
import binascii
import logging
import os
import time
import xmlrpc.client

import click
import putiopy


class PutioAria2cDownloader():
    """Put.io Aria2c downloader
    """

    def __init__(self, **kwargs):
        """Putio Aria2c Downloader

        Attributes:
            oauth_token (str): put.io oauth token
            keep_folder_structure (bool): Whether or not to keep the same folder structure as
                on put.io
            root_watch_dir (str): ID of root folder on put.io to check for watched folders
            aria2c_secret_token (str): aria2c rpc secret token
            root_download_dir (int): Which folder id (on put.io) to start recursing from
            post_process_dir (str): Where to move completed downloads
            watch_list (dict): folder names to watch inside root_download_dir on put.io
            rpc_url (str): URL for aria2c RPC interface
        """
        self.logger = logging.getLogger('putio.' + __name__)
        if kwargs.get('oauth_token', None):
            self.oauth_token = kwargs.get('oauth_token')
        if kwargs.get('keep_folder_structure', None):
            self.keep_folder_structure = kwargs.get('keep_folder_structure')
        if kwargs.get('root_watch_dir', None):
            self.root_watch_dir = kwargs.get('root_watch_dir')
        if kwargs.get('aria2c_secret_token', None):
            self.aria2c_secret_token = kwargs.get('aria2c_secret_token')
        if kwargs.get('root_download_dir', None):
            self.root_download_dir = kwargs.get('root_download_dir')
        if kwargs.get('post_process_dir', None):
            self.post_process_dir = kwargs.get('post_process_dir')
        if kwargs.get('watch_folders', None):
            self.watch_list = kwargs.get('watch_folders')
        if kwargs.get('rpc_url', None):
            self.rpc_url = kwargs.get('rpc_url')

    def download_all_in_watchlist(self, root_watch_dir: int = 0):
        """Searches for files to download in all watched folders

        Args:
            root_watch_dir: put.io directory id to start looking for watched folders
        """
        click.echo('Searching for files to download from put.io')
        client = putiopy.Client(self.oauth_token)
        files = client.File.list(parent_id=root_watch_dir)
        for _file in files:
            if (_file.content_type == 'application/x-directory'
                    and _file.name in self.watch_list):
                self.download_all_in_folder(
                    client, _file, path=_file.name, download_dir=self.root_download_dir
                )
            else:
                click.echo('Folder {} not in watchlist'.format(_file.name))
        client.close()

    def download_all_in_folder(
            self,
            client: putiopy.Client,
            folder,
            path: str = '',
            download_dir: str = None
    ):
        """Download all in folder

        Args:
            client: put.io client object
            folder (putiopy.File): folder on put.io to download from
            path: path to the folder
            download_dir: path to place downloads
        """
        click.echo('Downloading everything in {}'.format(folder.name))
        if not self.keep_folder_structure:
            download_dir = self.root_download_dir
        files = client.File.list(folder.id)
        for _file in files:
            if _file.content_type == 'application/x-directory':
                folderpath = '/'.join([path, _file.name])
                try:
                    click.echo(folderpath)
                    click.echo(
                        'Making directory {}{}'.format(self.post_process_dir, folderpath)
                    )
                    os.makedirs(''.join([self.post_process_dir, folderpath]))
                except FileNotFoundError:
                    raise click.ClickException('Couldn\'t create directory')
                except FileExistsError:
                    click.echo(
                        'Folder {} already exists'.format(
                            ''.join([self.post_process_dir, folderpath])
                        )
                    )
                self.download_all_in_folder(client, _file, folderpath, download_dir=download_dir)
                click.echo('Files from {} sent to aria2c'.format(folderpath))
                self.cleanup_empty_folders(client, _file)
            else:
                download_link = _file.get_download_link()
                if not download_dir:
                    download_dir = ''
                completed = self.add_uri(
                    download_link, directory='/'.join([download_dir, path])
                )
                if completed:
                    click.echo('File {} downloaded successfully by aria'.format(_file.name))
                    _file.delete(True)
                    download_path = '/'.join([download_dir, path, _file.name])
                    destination_path = '/'.join([self.post_process_dir, path, _file.name])
                    os.rename(download_path, destination_path)
                else:
                    click.echo(
                        'File {} didn\'t download successfully with aria'.format(_file.name)
                    )
        if not files:
            click.echo('No files to download in {}'.format(folder.name))

    def cleanup_empty_folders(self, client: putiopy.Client, folder):
        """Cleanup empty folders

        Args:
            client: putio client library client object
            folder (putiopy.File): folder to cleanup
        """
        click.echo('Cleaning up...')
        files = client.File.list(folder.id)
        if not files:
            if folder.name not in self.watch_list:
                folder.delete(True)
                click.echo('Deleted {} from put.io'.format(folder.name))

    def add_uri(self, uri: str, directory: str = None) -> bool:
        """Add URI to aria2c

        Args:
            uri: URI to add to aria2c
            directory: directory to place the download

        Returns:
            status: whether URI was added and completed successfully
        """
        token = 'token:' + self.aria2c_secret_token
        if not self.keep_folder_structure:
            directory = self.root_download_dir
        click.echo('Adding URI {} to {}'.format(uri, directory))
        proxy = xmlrpc.client.ServerProxy(self.rpc_url)
        opts = {
            'dir': directory,
            'file-allocation': 'falloc',
            'always-resume': 'true',
            'max-connection-per-server': '4',
            'check-integrity': 'true'
        }
        gid = proxy.aria2.addUri(token, [uri], opts)
        loop = True
        while loop:
            time.sleep(2)
            status = proxy.aria2.tellStatus(
                token, gid, ['gid', 'status', 'errorCode', 'errorMessage']
            )
            self.logger.debug(status)
            if status['status'] == 'complete':
                loop = False
                return True
            if status['status'] == 'error':
                loop = False
            if status['status'] == 'removed':
                loop = False
        return False

    @staticmethod
    def crc(filename: str) -> str:
        """CRC32 check

        Args:
            filename: Name of file for which to calculate crc32

        Returns:
            value: crc32 value
        """
        click.echo('Checking CRC32...')
        buf = open(filename, 'rb').read()
        buf32 = (binascii.crc32(buf) & 0xFFFFFFFF)
        return '%08X' % buf32
