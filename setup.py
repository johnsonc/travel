import os
from distutils.core import setup

VERSION = '0.2' 

packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)
    
for dirpath, dirnames, filenames in os.walk('travel'):
    # Ignore dirnames that start with '.'
    if os.path.basename(dirpath).startswith('.'):
        continue
    if '__init__.py' in filenames:
        pkg = dirpath.replace(os.path.sep, '.')
        if os.path.altsep:
            pkg = pkg.replace(os.path.altsep, '.')
        packages.append(pkg)
    elif filenames:
        data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])

setup(
    name='django-travel',
    version=VERSION,
    url='https://github.com/dakrauth/travel',
    description='A travelogue and bucket list app for Django',
    author='David A Krauth',
    author_email='dakrauth@gmail.com',
    platforms=['any'],
    license='New BSD License',
    packages=packages,
    data_files=data_files,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities',
    ]
)