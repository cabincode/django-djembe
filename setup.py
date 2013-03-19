from setuptools import setup

djembe = __import__('djembe')

with open('README.rst') as file:
    long_description = file.read()

setup(
    author='John Hensley',
    author_email='john@cabincode.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: Public Domain',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Communications :: Email',
        'Topic :: Security :: Cryptography',
    ],
    description=djembe.__doc__,
    long_description=long_description,
    download_url='http://github.com/cabincode/django-djembe/downloads',
    install_requires=[
        'Django>=1.4',
        'M2Crypto',
        'South'
    ],
    name='django-djembe',
    packages=[
        'djembe',
        'djembe.migrations',
        'djembe.tests'
    ],
    package_data={
        'djembe': [
            'README.rst',
            'LICENSE.txt',
        ],
    },
    tests_require=[
        'Django>=1.4',
        'M2Crypto',
        'South',
        'coverage',
        'django_coverage'
    ],
    test_suite='tests.main',
    url='http://github.com/cabincode/django-djembe',
    version=djembe.get_version(),
)
