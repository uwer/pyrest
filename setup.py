from setuptools import setup, find_packages

from pyrest import __version__

setup(
    name='pyrest',
    version=__version__,
    package_dir = {"": "src"},
    
    url='https://github.com/uwer/pyrest',
    author='UR',
    author_email='ur@gmail.com',
    install_requires=[
        "six",
        "certifi",
        "mimetypes",        
    ],
    
    packages=find_packages(where='src'),
    
)