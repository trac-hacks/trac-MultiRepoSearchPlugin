from setuptools import setup

try:
    long_description = open("README.txt").read()
except:
    long_description = ''

setup(name='trac-MultiRepoSearchPlugin',
      version='0.1',
      description="Search the text of source code in your Trac repositories (0.12 and up)",
      long_description=long_description,
      packages=['multireposearch'],
      author='Ethan Jucovy',
      author_email='ejucovy@gmail.com',
      url="http://trac-hacks.org/wiki/MultiRepoSearchPlugin",
      install_requires=["tracsqlhelper"],
      license='BSD',
      entry_points = {'trac.plugins': ['multireposearch = multireposearch']})
