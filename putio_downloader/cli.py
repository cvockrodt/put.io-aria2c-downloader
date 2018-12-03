"""Main CLI entrypoint for put.io downloader
"""
import logging
import os
import xmlrpc
from typing import Union

import click
import click_config_file
import putiopy

from . import PutioAria2cDownloader, __version__

LOGGER = logging.getLogger('putio.' + __name__)


def print_version(
        ctx: click.core.Context,
        param: Union[click.core.Option, click.core.Parameter],
        value: Union[bool, int, str]
):
    """Print version callback method

    Args:
        ctx: click context
        param: click param
        value: click value
    """
    if param == 'test':
        return
    if not value or ctx.resilient_parsing:
        return
    click.echo('Putio Aria2c Downloader version {}'.format(__version__))
    ctx.exit()


@click.command()
@click.option('--oauth-token', prompt=True, hide_input=True, required=True)
@click.option('--keep-folder-structure', default=True, is_flag=True, prompt=True)
@click.option('--root-watch-dir', default=0, prompt=True, required=True)
@click.option('--aria2c-secret-token', prompt=True, hide_input=True, required=True)
@click.option('--root-download-dir', default='/tmp', prompt=True, required=True)
@click.option('--post-process-dir', default=os.getcwd(), prompt=True, required=True)
@click.option('--watch-folders', prompt=True, required=True)
@click.option('--rpc-url', default='http://localhost:6800/rpc', prompt=True, required=True)
@click.option('--version', is_flag=True, callback=print_version)
@click.option('--quiet', '-q', default=False, is_flag=True)
@click.option('--verbose', '-v', default=False, is_flag=True)
@click_config_file.configuration_option()
def main(**kwargs):
    """CLI entrypoint for put.io downloader
    """
    if kwargs.get('quiet'):
        LOGGER.setLevel(logging.ERROR)
    elif kwargs.get('verbose'):
        LOGGER.setLevel(logging.DEBUG)
    else:
        LOGGER.setLevel(logging.INFO)

    try:
        downloader = PutioAria2cDownloader(**kwargs)
        downloader.download_all_in_watchlist()
    except putiopy.ClientError:
        raise click.ClickException('There was a problem connecting to put.io')
    except xmlrpc.client.ProtocolError:
        raise click.ClickException('There was a problem connecting to the aria2c xmlrpc interface')
    except xmlrpc.client.Fault:
        raise click.ClickException(
            'There was a problem authenticating to the aria2c xmlrpc interface'
        )
