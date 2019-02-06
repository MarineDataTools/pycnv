0.3.8:
        - added first draft of gui
0.3.7:
        - first version with a rudimentary plot routine
	- changed data from recarray to dictionary
0.3.6:
        - cdata has a copy of the 'p' field for convenience
	- oxygen is now correctly read in as standard name
	- oxygen saved in ml/l is converted to umol/l and saved in cdata
0.3.5:
        - Custom header functionality added
0.3.4:
        - Added requirements to setup.py
        - changed CHANGELOG to CHANGELOG.rst

0.3.3:
        - Changed pycnv.date to start_time field
	- Timezone is now added to date fields
0.3.2:
	- oxygen conversion routines added
0.3.1:
	- added pycnv.regions_baltic for testing of CTD cast is in the Baltic
	- added a conversion of IPTS-68 to T90 and S7m to mS/cm
	- added pycnv.get_all_valid_files()
	- added pycnv.get_stations()
	- added pycnv/test/plot_baltic_test_regions.py
	- added pycnv/test/make_netcdf.py
	- several small stability changes
