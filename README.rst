
Python toolbox to read and process Seabird_ cnv files.

.. _Seabird: http://www.seabird.com/

These text files are the standard output files of the Seabird CTD software.

The main purpose for pycnv is to create a standardised interface for
slightly differing naming conventions of sensors in the cnv files and
the usage of the `Gibb Sea Water Toolbox (gsw) <https://github.com/TEOS-10/GSW-Python>`_
for the calculation of all
derived parameters as practical salinity, absolute salinity, potential
and conservative temperature or density. For this purpose pycnv does
only need pressure, conductivity and temperature, all other properties
will be derived from these. Furthermore pycnv will take care for a
different absolute salinity computation in the Baltic Sea, by
automatically checking of a cast was made in the Baltic Sea and
choosing the correct function.


Install
-------

The package was developed using python 3.5+, it might work with
earlier versions, but its not supported. The newest
`Gibb Sea Water Toolbox (gsw) <https://github.com/TEOS-10/GSW-Python>`_
depends also on python 3.5+, pycnv heavily depends on the gsw toolbox. It
therefore strongly recommended to use python 3.5+.

User
____


Install as a user using pip

.. code:: bash
	  
   pip install pycnv

Install as a user from the repository

.. code:: bash
	  
   python setup.py install --user

Uninstall as a user
   
.. code:: bash
	  
   pip uninstall pycnv



Developer
_________

Install as a developer

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
  cdata. E.g. cdata['SA00']. The code used to compute the properties
  are
  
  .. code:: python
	    
            SP = gsw.SP_from_C(data['C' + isen], T, data['p'])
            SA = gsw.SA_from_SP(SP,data['p'],lon = lon, lat = lat)
            if(baltic == True):
	        SA = gsw.SA_from_SP_Baltic(SA,lon = lon, lat = lat)
            
	    PT = gsw.pt0_from_t(SA, T, data['p'])
            CT = gsw.CT_from_t(SA, T, data['p'])        
            pot_rho = gsw.pot_rho_t_exact(SA, T, data['p'], p_ref)

- The cnv object provides standard entries for pressure (cnv.p),
  temperature (cnv.T), conservative temperature (cnv.CT), practical
  salinity (cnv.SP), absolute salinity (cnv.SA), potential density
  (cnv.pot_rho), oxygen (cnv.oxy). The units have the extension
  _units, i.e. cnv.p_units

- The module checks if the cast was made in the Baltic Sea, if so, the
  modified Gibbs sea water functions are automatically used.

- The package provides scripts to search a given folder for cnv files
  and can create a summary of the folder in a csv format easily
  readable by python or office programs. The search can be refined by
  a location or a predefined station.

- Possibility to provide an own function for parsing custom header
  information.

- Plotting of the profile using `matplotlib <https://matplotlib.org>`_



USAGE
-----

The package installs the executables:

- pycnv

- pycnv_sum_folder

  
EXAMPLES 
--------
Plot the absolute salinity and oxygen of a CTD cast:

.. code:: python
	  
	  import pycnv
	  import pylab as pl 
	  fname = 'test.cnv' # Some CTD cast

	  cnv = pycnv.pycnv(fname)
	  print('Test if we are in the Baltic Sea (usage of different equation of state): ' + str(cnv.baltic))
	  print('Position of cast is: Longitude:', cnv.lon,'Latitude:',cnv.lat)
	  print('Time of cast was:', cnv.date)
	  print('Number of sensor entries (len(cnv.data.keys())):',len(cnv.data.keys()))
	  print('Names of sensor entries (cnv.data.keys()):',cnv.data.keys())

	  # Get data of entry
	  key0 = list(cnv.data.keys())[0]
	  data0 = cnv.data[key0]

	  # Get derived data:
	  keyd0 = list(cnv.cdata.keys())[0]
	  datad0 = cnv.cdata[keyd0]
	  # Get unit of derived data
	  datad0_unit = cnv.cunits[keyd0]

	  # Standard names are mapped to 
	  # cnv.p,cnv.CT,cnv.T,cnv.SP,cnv.oxy
	  # units are _unit, e.g. cnv.p_unit

	  # Plot standard parameters
	  pl.figure(1)
	  pl.clf()
	  pl.subplot(1,2,1)
	  pl.plot(cnv.SA,cnv.p)
	  pl.xlabel('Absolute salinity [' + cnv.SA_unit + ']')
	  pl.ylabel('Pressure [' + cnv.p_unit + ']')
	  pl.gca().invert_yaxis()

	  pl.subplot(1,2,2)
	  pl.plot(cnv.oxy,cnv.p)
	  pl.plot(cnv.cdata['oxy0'],cnv.p)
	  pl.plot(cnv.cdata['oxy1'],cnv.p)
	  pl.xlabel('Oxygen [' + cnv.oxy_unit + ']')
	  pl.ylabel('Pressure [' + cnv.p_unit + ']')
	  pl.gca().invert_yaxis()

	  pl.show()


	  
Lists all predefined stations (in terminal):

.. code:: bash
	  
	  pycnv_sum_folder --list_stations


Makes a summary of the folder called cnv_data of all casts around
station TF0271 with a radius of 5000 m, prints it to the terminal and
saves it into the file TF271.txt  (in terminal):

.. code:: bash
	  
	  pycnv_sum_folder --data_folder cnv_data --station TF0271 5000 -p -f TF271.txt


Show and plot conservative temperature, salinity and potential density of a cnv file into a pdf:

.. code:: bash
	  
	  pycnv --plot show,save,CT00,SA00,pot_rho00 ctd_cast.cnv


Interpolate all CTD casts on station TF0271 onto the same pressure axis and make a netCDF out of it:

see code pycnv/test/make_netcdf.py


Devices tested 
--------------

- SEACAT (SBE16) V4.0g

- MICROCAT (SBE37)

- SBE 11plus V 5.1e

- SBE 11plus V 5.1g

- Sea-Bird SBE 9 Software Version 4.206

	  



