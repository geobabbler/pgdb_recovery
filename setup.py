#!/usr/bin/env python3
"""
Setup script for Personal Geodatabase to CSV Converter
"""

from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ''

setup(
    name='pgdb_recovery',
    version='1.0.0',
    description='Convert ESRI Personal Geodatabase (.mdb) files to CSV with WKT geometry',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    author='Bill Dollins',
    author_email='bill@dollins.net',
    url='https://github.com/geobabbler/pgdb_recovery',
    license='MIT',
    
    packages=find_packages(),
    
    install_requires=[
        'pyodbc>=4.0.0',
    ],
    
    python_requires='>=3.6',
    
    entry_points={
        'console_scripts': [
            'pgdb_recovery=pgdb.read_pgdb_geometry:main',
        ],
    },
    
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: GIS',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: OS Independent',
    ],
    
    keywords='gis geodatabase esri mdb shapefile wkt csv qgis',
    
    project_urls={
        'Bug Reports': 'https://github.com/geobabbler/pgdb_recovery/issues',
        'Source': 'https://github.com/geobabbler/pgdb_recovery',
    },
)