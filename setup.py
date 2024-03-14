from setuptools import setup, find_packages



setup(
    name='pyrest',
    version='0.9',
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