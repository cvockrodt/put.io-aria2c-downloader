"""Setup file
"""
import re
from setuptools import find_packages, setup


def _read_long_description():
    try:
        with open('readme.md') as fd:
            return fd.read()
    except Exception:
        return None


with open('putio_downloader/__init__.py', 'r') as fv:
    version = re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
        fv.read(),
        re.MULTILINE
    ).group(1)

with open('requirements.txt', 'r') as fv:
    requirements = fv.read().strip().split('\n')

setup(
    name='putio-downloader',
    version=version,
    url='https://github.com/cvockrodt/put.io-aria2c-downloader',
    author='Casey Vockrodt',
    author_email='casey.vockrodt@gmail.com',
    description='Download all files from your put.io account recursively with aria2c',
    long_description=_read_long_description(),
    packages=find_packages(exclude='tests'),
    license='MIT',
    install_requires=requirements,
    entry_points='''
        [console_scripts]
        putio-download=putio_downloader.cli:main
    ''',
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ]
)
