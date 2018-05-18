from setuptools import setup, find_packages

from codecs import open
from os import path

import mqttgateway.version

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='mqttgateway',
    version=mqttgateway.version.version,
    description='Framework for MQTT Gateways',
    long_description=long_description,
    #long_description_content_type='text/x-rst', # apparently it is optional if rst
    url='http://mqttgateway.readthedocs.io/en/latest/',
    author='Pier Paolo Taddonio',
    author_email='paolo.taddonio@empiluma.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        ],
    keywords='mqtt gateway',
    packages=find_packages(),
    install_requires=['paho-mqtt >= 1.3.1'],
    package_data={'': ['*.conf', '*.json']},
    #exclude_package_data={'': ['README.*']},
    entry_points={'console_scripts': ['dummy2mqtt = mqttgateway.dummy.dummy2mqtt:main']}
    #              'console_scripts': ['entry2mqtt = mqttgateway.entry.entry2mqtt:__main__']}
)