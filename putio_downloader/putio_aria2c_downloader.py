"""Put.io Aria2c Downloader."""
import binascii
import logging
import os
import shutil
import tempfile
import time
import xmlrpc.client

import click
import putiopy


class PutioAria2cDownloader():
    """Put.io Aria2c downloader."""

    def __init__(self, **kwargs):
        """Put.io Aria2c downloader.

        Attributes:
            keep_folder_structure (bool): keep the same structure as on put.io
            aria2c_secret_token (str): aria2c rpc secret token
            incomplete_dir (int): put.io folder to start recursing from
            complete_dir (str): Where to move completed downloads
            watch_list (dict): folders to watch in incomplete_dir on put.io
            putio_client: putio.py library client object
            aria_client: aria2c xmlrpc client object

        """
        self.logger = logging.getLogger('putio.' + __name__)

        self.keep_folder_structure = kwargs.get('keep_folder_structure', True)
        aria2c_secret_token = kwargs.get("aria2c_secret_token")
        self.aria2c_secret_token = f'token:{aria2c_secret_token}'
        self.incomplete_dir = kwargs.get('incomplete_dir', tempfile.mkdtemp())
        self.complete_dir = kwargs.get('complete_dir', os.getcwd())
        self.watch_list = kwargs.get('watch_folders', [])

        self.putio_client = putiopy.Client(
            kwargs.get('oauth_token'),
            use_retry=True,
            timeout=10
        )
        self.aria_client = xmlrpc.client.ServerProxy(kwargs.get('rpc_url'))

    def download_all_in_watchlist(
            self, root_watch_dir: int = 0, clear_results: bool = False):
        """Search for files to download in all watched folders.

        Args:
            root_watch_dir: put.io folder id to look in for watched folders
            clear_results: should we remove all download results from aria2c?

        """
        click.echo('Searching for files to download from put.io')
        files = self.putio_client.File.list(parent_id=root_watch_dir)
        for folder in files:
            if (
                    folder.content_type == 'application/x-directory' and
                    folder.name in self.watch_list
            ):
                self.download_all_in_folder(folder, path=folder.name)
            else:
                click.echo(f'Folder {folder.name} not in watchlist')
        self.putio_client.close()
        if clear_results:
            self.aria_client.aria2.purgeDownloadResult(
                self.aria2c_secret_token)

    def download_all_in_folder(self, folder, path: str = '',):
        """Download all in folder.

        Args:
            folder (putiopy.File): folder on put.io to download from
            path: path to the folder

        """
        click.echo(f'Downloading everything in {folder.name}')
        files = self.putio_client.File.list(folder.id)
        for _file in files:
            if _file.content_type == 'application/x-directory':
                self.process_folder(_file, path)
            else:
                self.process_file(_file, path)
        if not files:
            click.echo(f'No files to download in {folder.name}')

    def process_folder(self, folder, path: str):
        """Process Folder.

        Args:
            folder (putiopy.Client.File): put.io file object
            path (str): path where folder lives

        """
        folderpath = os.path.join(path, folder.name)
        dest_dir = os.path.join(self.complete_dir, folderpath)
        try:
            click.echo(folderpath)
            click.echo(f'Making directory {folderpath}')
            os.makedirs(dest_dir)
        except FileNotFoundError:
            raise click.ClickException('Couldn\'t create directory')
        except FileExistsError:
            click.echo(f'Folder {dest_dir} already exists')
        self.download_all_in_folder(folder, folderpath)
        click.echo(f'Files from {folderpath} sent to aria2c')
        self.cleanup_empty_folders(folder)

    def process_file(self, _file, path: str,):
        """Process Folder.

        Args:
            _file (putiopy.Client.File): put.io file object
            path (str): path where folder lives

        """
        directory = os.path.join(self.incomplete_dir, path)
        completed = self.add_uri(
            _file.get_download_link(), directory=directory)
        if completed:
            click.echo(f'File {_file.name} downloaded successfully by aria')
            _file.delete(True)
            download_path = os.path.join(directory, _file.name)
            destination_path = os.path.join(
                self.complete_dir, path, _file.name)
            shutil.move(download_path, destination_path)
            try:
                os.rmdir(directory)
            except FileNotFoundError:
                click.echo(f'Tried to rm {directory} but it wasn\'t empty')
        else:
            click.echo(f'aria2c didn\'t download {_file.name} successfully')

    def cleanup_empty_folders(self, folder):
        """Cleanup empty folders.

        Args:
            folder (putiopy.File): folder to cleanup

        """
        click.echo('Cleaning up...')
        files = self.putio_client.File.list(folder.id)
        if not files:
            if folder.name not in self.watch_list:
                folder.delete(True)
                click.echo(f'Deleted {folder.name} from put.io')

    def add_uri(self, uri: str, directory: str) -> bool:
        """Add URI to aria2c.

        Args:
            uri: URI to add to aria2c
            directory: directory to place the download

        Returns:
            status: whether URI was added and completed successfully

        """
        if not self.keep_folder_structure:
            directory = self.incomplete_dir
        click.echo(f'Adding URI {uri} to {directory}')

        opts = {
            'dir': directory,
            'file-allocation': 'falloc',
            'always-resume': 'true',
            'max-connection-per-server': '4',
            'check-integrity': 'true'
        }
        gid = self.aria_client.aria2.addUri(
            self.aria2c_secret_token, [uri], opts)
        loop = True
        while loop:
            time.sleep(2)
            status = self.aria_client.aria2.tellStatus(
                self.aria2c_secret_token,
                gid,
                ['gid', 'status', 'errorCode', 'errorMessage']
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
        """Check CRC32 value.

        Args:
            filename: Name of file for which to calculate crc32

        Returns:
            value: crc32 value

        """
        click.echo('Checking CRC32...')
        buf = open(filename, 'rb').read()
        buf32 = (binascii.crc32(buf) & 0xFFFFFFFF)
        return '%08X' % buf32
