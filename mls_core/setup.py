"""
Setup script for django-mls-core package.

To create a distributable package:
    python setup.py sdist bdist_wheel

To install locally for development:
    pip install -e .

To upload to PyPI:
    twine upload dist/*
"""

from setuptools import setup, find_packages
import os


# Read long description from README
def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()


setup(
    name='django-mls-core',
    version='1.0.0',
    description='Multi-Level Security (MLS) for Django - Reusable app for enforcing MLS access control',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/yourusername/django-mls-core',
    license='MIT',

    packages=['mls_core'],
    include_package_data=True,
    zip_safe=False,

    install_requires=[
        'Django>=3.2',
        'django-crum>=0.7.9',
    ],

    python_requires='>=3.8',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 3.2',
        'Framework :: Django :: 4.0',
        'Framework :: Django :: 4.1',
        'Framework :: Django :: 4.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Security',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],

    keywords='django mls multi-level-security access-control security clearance classification',

    project_urls={
        'Documentation': 'https://github.com/yourusername/django-mls-core#readme',
        'Source': 'https://github.com/yourusername/django-mls-core',
        'Tracker': 'https://github.com/yourusername/django-mls-core/issues',
    },
)
