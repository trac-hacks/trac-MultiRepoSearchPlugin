from setuptools import setup

try:
    long_description = open("README.txt").read()
except:
    long_description = ''
try:
    long_description += open("CHANGES.txt").read()
except:
    pass

setup(name='trac-MultiRepoSearchPlugin',
      version='0.2',
      description="Search the text of source code in your Trac repositories (0.12 and up)",
      long_description=long_description,
      packages=['multireposearch'],
      author='Ethan Jucovy',
      author_email='ejucovy@gmail.com',
      url="http://trac-hacks.org/wiki/MultiRepoSearchPlugin",
      install_requires=["tracsqlhelper"],
      license='BSD',
      entry_points = {'trac.plugins': ['multireposearch = multireposearch']})
