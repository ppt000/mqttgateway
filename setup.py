''' setup file for mqttgateway '''

from setuptools import setup

from mqttgateway import VERSION

# Get the long description from the README file
with open('README.rst') as f:
    long_description = f.read()

setup(
    name='mqttgateway',
    version=VERSION,
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
    packages=['mqttgateway'],
    package_data={'mqttgateway': ['res/*.cfg', 'res/*.json', 'res/*.md']},
    install_requires=['paho-mqtt >= 1.6.1'],
    entry_points={'console_scripts': ['dummy2mqtt = mqttgateway.__main__:main']}
)
