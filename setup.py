"""Setup file
"""
from setuptools import find_packages, setup


def _read_long_description():
    try:
        with open('README.md') as fd:
            return fd.read()
    except Exception:
        return None


with open('requirements.txt', 'r') as fv:
    requirements = fv.read().strip().split('\n')

setup(
    name='putio-downloader',
    version='3.0.1',
    url='https://github.com/cvockrodt/put.io-aria2c-downloader',
    author='Casey Vockrodt',
    author_email='casey.vockrodt@gmail.com',
    description='Download all files from your put.io account recursively with aria2c',
    long_description=_read_long_description(),
    long_description_content_type="text/markdown",
    packages=find_packages(exclude='tests'),
    license='MIT',
    install_requires=requirements,
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ]
)
