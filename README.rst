
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



USAGE
-----

The package installs the executables:

- pycnv

- pycnv_sum_folder

  
Example usage 
  
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
	  
