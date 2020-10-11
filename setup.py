#!/usr/bin/env python3

from setuptools import setup

from django_migrations_diff import get_version

with open('README.rst') as f:
    readme = f.read()

setup(
    name='django-migrations-diff',
    version=get_version(),
    description='CLI for comparing Django migrations between two snapshots.',
    long_description=readme,
    author='Denis Krumko',
    author_email='dkrumko@gmail.com',
    url='https://github.com/deniskrumko/django-migrations-diff',
    license="MIT",
    entry_points={
        'console_scripts': [
            'mdiff = django_migrations_diff.main:main',
        ],
    },
    packages=['django_migrations_diff'],
    python_requires=">=3.6",
    install_requires=['requests'],
    keywords='CLI, Django, Migrations, Diff',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities',
    ],
)
