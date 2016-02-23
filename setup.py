# -*- coding: utf-8 -*-
"""Setup file for the PenatesServer project.
"""
from __future__ import unicode_literals

import codecs
import os.path
import re

from setuptools import setup, find_packages


# avoid a from penatesserver import __version__ as version (that compiles penatesserver.__init__
#   and is not compatible with bdist_deb)
version = None
for line in codecs.open(os.path.join('penatesserver', '__init__.py'), 'r', encoding='utf-8'):
    matcher = re.match(r"""^__version__\s*=\s*['"](.*)['"]\s*$""", line)
    version = version or matcher and matcher.group(1)

# get README content from README.md file
with codecs.open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as fd:
    long_description = fd.read()

entry_points = {'console_scripts': ['penatesserver-manage = djangofloor.scripts:manage',
                                    'penatesserver-celery = djangofloor.scripts:celery',
                                    'penatesserver-uswgi = djangofloor.scripts:uswgi',
                                    'penatesserver-gunicorn = djangofloor.scripts:gunicorn']}

install_requires = ['djangofloor', 'djangorestframework', 'markdown', 'django-filter', 'pygments',
                    'django-ldapdb', 'netaddr', 'jinja2']
setup(
    name='penatesserver',
    version=version,
    description='No description yet.',
    long_description=long_description,
    author='flanker',
    author_email='flanker@19pouces.net',
    license='CeCILL-B',
    url='https://github.com/d9pouces/Penates-Server',
    entry_points=entry_points,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    test_suite='penatesserver.tests',
    install_requires=install_requires,
    setup_requires=[],
    classifiers=[],
)
