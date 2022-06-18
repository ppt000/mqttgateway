''' setup file for mqttgateway '''

from setuptools import setup#, find_packages

from mqttgateway import __version__

# Get the long description from the README file
with open('README.rst') as f:
    long_description = f.read()

setup(
    name='mqttgateway',
    version=__version__,
    description='Framework for MQTT Gateways.',
    long_description=long_description,
    #long_description_content_type='text/x-rst',
    url='http://mqttgateway.readthedocs.io/en/latest/',
    author='Pier Paolo Taddonio',
    author_email='paolo.taddonio@empiluma.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Embedded Systems',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.9'
        ],
    keywords='mqtt gateway',
    packages=['mqttgateway'],#find_packages(),
    install_requires=['paho-mqtt >= 1.6.1'],
    package_data={'': ['*.conf', '*.json']},
    entry_points={'console_scripts': ['dummy2mqtt = mqttgateway.dummy_start:main']}
)
