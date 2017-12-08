from .pycnv import *
from .pycnv_sum_folder import get_all_valid_files, get_stations


with open(version_file) as version_f:
   version = version_f.read().strip()

__version__ = version
