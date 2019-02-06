from setuptools import setup
import os

ROOT_DIR='pycnv'
with open(os.path.join(ROOT_DIR, 'VERSION')) as version_file:
    version = version_file.read().strip()

setup(name='pycnv',
      version=version,
      description='Tools to convert Seabird cnv textfiles',
      url='https://github.com/MarineDataTools/pycnv',
      author='Peter Holtermann',
      author_email='peter.holtermann@io-warnemuende.de',
      license='GPLv03',
      packages=['pycnv'],
      scripts = [],
      entry_points={ 'console_scripts': ['pycnv_cmd=pycnv.pycnv:main', 'pycnv_sum_folder=pycnv.pycnv_sum_folder:main', 'pycnv=pycnv.gui.pycnv_gui:main']},
      package_data = {'':['VERSION','stations/iow_stations.yaml','rules/standard_names.yaml']},
      install_requires=[ 'gsw', 'pyproj','pytz','pyaml' ],
      zip_safe=False)


# TODO Depends on gsw, pyproj, pytz
