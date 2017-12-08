
Python toolbox to read and process Seabird_ cnv files.

.. _Seabird: http://www.seabird.com/

These text files are the standard output files of the Seabird CTD software.


Install
-------

Developer
_________

Install as a user

.. code:: bash
	  
   python setup.py develop --user

Uninstall as a user
   
.. code:: bash
	  
pip uninstall pycnv


FEATURES
--------

- The data can be accessed by the original names defined in the cnv
  file in the named array called data. E.g. header name "# name 11 =
  oxsatML/L: Oxygen Saturation, Weiss [ml/l]" can be accessed like
  this: data['oxsatML/L'].

- Standard parameters (Temperature, Conductivity, pressure, oxygen)
  are mapped to standard names. E.g. data['T0'] for the first
  temperature sensor and data['C1'] for the second conductivity sensor.

- If the standard parameters (C0,T0,p), (C1,T1,p) are available the
  Gibbs Sea water toolbox is used to calculate absolute salinity, SA,
  conservative temperature, CT, and potential temperature pt. The data
  is stored in a second field called computed data:
  cdata. E.g. cdata['SA00'].

- The module checks if the cast was made in the Baltic Sea, if so, the
  modified Gibbs sea water functions are automatically used.

- The package provides scripts to search a given folder for cnv files
  and can create a summary of the folder in a csv format easily
  readable by python or office programs. The search can be refined by
  a location or a predefined station.



USAGE
-----

The package installs the executables:

- pycnv

- pycnv_sum_folder

  
EXAMPLES 
--------
Plot the in Situ temperature and the conservative temperature of a CTD cast:

.. code:: python
	  
	  import pycnv
	  import pylab as pl
	  fname='test'cnv' # A sebaird cnv file
	  p = pycnv.pycnv(fname)
	  pl.figure(1)
	  pl.clf()
	  pl.subplot(1,2,1)
	  pl.plot(p.data['T'],p.date['p'])
	  pl.xlabel(p.units['T'])
	  pl.gca().invert_yaxis()	  
	  pl.subplot(1,2,2)
	  pl.plot(p.cdata['CT'],p.date['p'])
	  pl.xlabel(p)
	  pl.gca().invert_yaxis()

	  
Lists all predefined stations (in terminal):

.. code:: python
	  
	  pycnv_sum_folder --list_stations


Makes a summary of the folder called cnv_data of all casts around
station TF0271 with a radius of 5000 m, prints it to the terminal and
saves it into the file TF271.txt  (in terminal):

.. code:: python
	  
	  pycnv_sum_folder --data_folder cnv_data --station TF0271 5000 -p -f TF271.txt


