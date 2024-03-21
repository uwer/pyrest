from setuptools import setup, find_packages


## 
## this sets up the client only!

setup(
    name='pyrest',
    version='0.9',
    package_dir = {"": "src"},
    python_requires=">=3.8",
    
    url='https://github.com/uwer/pyrest',
    author='UR',
    author_email='ur@gmail.com',
    install_requires=[
        "six",
        "certifi",  
        "urllib3",    
    ],
    
    packages=find_packages(where='src'),
    
)