from setuptools import find_packages, setup

with open('README.md', 'r') as readme:
    long_description = readme.read()

setup(
    name='nearmap',
    packages=find_packages(),
    version='0.1.0',
    description='Python wrapper and extended functionality for Nearmap API',
    long_description=long_description,
    author='Nearmap Ltd',
    license='Apache 2.0',
)
