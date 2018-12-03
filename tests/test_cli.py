from click.testing import CliRunner

from putio_downloader import __version__
from putio_downloader.cli import main


def test_version():
    runner = CliRunner()
    result = runner.invoke(main, ['--version'])
    assert result.exit_code == 0
    assert result.output == 'Putio Aria2c Downloader version {}\n'.format(__version__)
