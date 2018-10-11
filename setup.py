#!/usr/bin/env python

from setuptools import setup

def read(path):
	with open(path) as f:
		return f.read()

setup(
	name='hypothesis-callables',
	version='0.0.1',
	description=('Hypothesis extension to allow generating dynamic callable objects'),
	long_description=read('README.rst'),
	author='Ruby Allison Rose',
	author_email='jtimmerman32@gmail.com',
	url='https://github.com/m3tior/hypothesis-callables',
	license='LGPL-2.1',
	keywords=('hypothesis', 'callables'),
	py_modules=['hypothesis_callables'],
	install_requires=[
		'hypothesis>=3.8',
	],
	setup_requires=['pytest-runner'],
	tests_require=['pytest'],
	classifiers=[
		'Development Status :: 4 - Beta',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: MIT License',
		'Programming Language :: Python :: 2',
		'Programming Language :: Python :: 2.7',
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.3',
		'Programming Language :: Python :: 3.4',
		'Programming Language :: Python :: 3.5',
		'Programming Language :: Python :: 3.6',
		'Programming Language :: Python :: Implementation :: CPython',
		'Programming Language :: Python :: Implementation :: PyPy',
	],
)
