"""Put.io Aria2c Downloader
"""
import binascii
import logging
import os
import tempfile
import time
import xmlrpc.client
import shutil

import click
import putiopy


class PutioAria2cDownloader():
    """Put.io Aria2c downloader
    """

    def __init__(self, **kwargs):
        """Putio Aria2c Downloader

        Attributes:
            keep_folder_structure (bool): Whether or not to keep the same folder structure as
                on put.io
            aria2c_secret_token (str): aria2c rpc secret token
            root_download_dir (int): Which folder id (on put.io) to start recursing from
            post_process_dir (str): Where to move completed downloads
            watch_list (dict): folder names to watch inside root_download_dir on put.io
            putio_client: putiopy library client object
            aria_client: aria2c xmlrpc client object
        """
        self.logger = logging.getLogger('putio.' + __name__)

        self.keep_folder_structure = kwargs.get('keep_folder_structure', True)
        self.aria2c_secret_token = 'token:%s' % kwargs.get('aria2c_secret_token', None)
        self.root_download_dir = kwargs.get('root_download_dir', tempfile.mkdtemp())
        self.post_process_dir = kwargs.get('post_process_dir', os.getcwd())
        self.watch_list = kwargs.get('watch_folders', [])

        self.putio_client = putiopy.Client(kwargs.get('oauth_token', None))
        self.aria_client = xmlrpc.client.ServerProxy(kwargs.get('rpc_url', None))

    def download_all_in_watchlist(self, root_watch_dir: int = 0, clear_results: bool = False):
        """Searches for files to download in all watched folders

        Args:
            root_watch_dir: put.io directory id to start looking for watched folders
            clear_results: should we clean up after ourselves and remove all download results
                from aria2c?
        """
        click.echo('Searching for files to download from put.io')
        files = self.putio_client.File.list(parent_id=root_watch_dir)
        for _file in files:
            if (_file.content_type == 'application/x-directory'
                    and _file.name in self.watch_list):
                self.download_all_in_folder(
                    _file, path=_file.name, download_dir=self.root_download_dir
                )
            else:
                click.echo('Folder {} not in watchlist'.format(_file.name))
        self.putio_client.close()
        if clear_results:
            self.aria_client.aria2.purgeDownloadResult(self.aria2c_secret_token)

    def download_all_in_folder(
            self,
            folder,
            path: str = '',
            download_dir: str = None
    ):
        """Download all in folder

        Args:
            folder (putiopy.File): folder on put.io to download from
            path: path to the folder
            download_dir: path to place downloads
        """
        click.echo('Downloading everything in {}'.format(folder.name))
        if not self.keep_folder_structure:
            download_dir = self.root_download_dir
        files = self.putio_client.File.list(folder.id)
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
                self.download_all_in_folder(_file, folderpath, download_dir=download_dir)
                click.echo('Files from {} sent to aria2c'.format(folderpath))
                self.cleanup_empty_folders(_file)
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
                    shutil.move(download_path, destination_path)
                else:
                    click.echo(
                        'File {} didn\'t download successfully with aria'.format(_file.name)
                    )
        if not files:
            click.echo('No files to download in {}'.format(folder.name))

    def cleanup_empty_folders(self, folder):
        """Cleanup empty folders

        Args:
            folder (putiopy.File): folder to cleanup
        """
        click.echo('Cleaning up...')
        files = self.putio_client.File.list(folder.id)
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

        if not self.keep_folder_structure:
            directory = self.root_download_dir
        click.echo('Adding URI {} to {}'.format(uri, directory))

        opts = {
            'dir': directory,
            'file-allocation': 'falloc',
            'always-resume': 'true',
            'max-connection-per-server': '4',
            'check-integrity': 'true'
        }
        gid = self.aria_client.aria2.addUri(self.aria2c_secret_token, [uri], opts)
        loop = True
        while loop:
            time.sleep(2)
            status = self.aria_client.aria2.tellStatus(
                self.aria2c_secret_token, gid, ['gid', 'status', 'errorCode', 'errorMessage']
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
