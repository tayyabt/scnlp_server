import sys
import os
import codecs

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup


packages = [
	'scnlp_server'
]


if sys.argv[-1] == 'publish':
	os.system('python3 setup.py sdist upload')  # bdist_wininst
	sys.exit()




with codecs.open('README.md', 'r', 'utf-8') as f:
	readme = f.read()


setup(
	name='scnlp_server',
	version='0.1a0',
	description='A simple server mode wrapper (and client) for the Stanford Core NLP and Stanford Sentiment Pipeline',
	long_description=readme,
	author='Tayyab Tariq',
	author_email='tayyabt@gmail.com',
	url='https://github.com/tayyabt/scnlp_server',
	packages=packages,
	include_package_data=True,
	license='MIT',
	zip_safe=False,
	classifiers=[
		'Programming Language :: Python :: 3',
		'Natural Language :: English',
		'Intended Audience :: Developers',
	],
)