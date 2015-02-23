import os, sys
from setuptools import setup, find_packages

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit(0)

VERSION = __import__('travel').get_version()

setup(
    name='django-travel',
    version=VERSION,
    url='https://github.com/dakrauth/travel',
    description='A travelogue and bucket list app for Django',
    author='David A Krauth',
    author_email='dakrauth@gmail.com',
    platforms=['any'],
    license='MIT License',
    packages=find_packages(),
    package_data={'travel': ['templates/travel/*', 'static/travel/*', 'media/img/*']},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities',
    ]
)