#
# Example script of the pycnv package to read in a bunch of CTD files,
# interpolate them to a common pressure axis and to create a netCDF
# containing conservative temperature and absolute salinity
#

import pycnv
import netCDF4
import logging
import time
from numpy import *
import sys
# cnv DATA_FOLDER (this hast to be changed to a local cnv folder)
DATA_FOLDER  = sys.argv[1]


# Get all stations
stations = pycnv.get_stations()
# Look for the TF0271 station
for s in stations:
    if('TF0271' in s['name']):
        station = [s['longitude'],s['latitude'],5000]
        break

print('Found a station:' + str(station))
t1 = time.time()
# Search in the DATA_FOLDER for cnv files
cnv_data = pycnv.get_all_valid_files(DATA_FOLDER, loglevel = logging.INFO, station=station)
#cnv_data = pycnv.get_all_valid_files(DATA_FOLDER, loglevel = logging.DEBUG)
cnv_files = cnv_data['files']

t2 = time.time()
dt = t2 - t1
print('Found ' + str(len(cnv_files)) + ' files in ' + '{:1.0f}'.format(dt) + ' seconds')

# The pressure axes we want to interpolate the data
p_int = arange(0,245,0.25)

# Empty lists containing the result hopefully soon
SA00_int    = []
CT00_int    = []
SA11_int    = []
CT11_int    = []
lon_all     = []
lat_all     = []
date_all    = []
timenum_all = []
timenum_unit = 'seconds since 1970-01-01 00:00:00' # This is the unix-time ...
for f in cnv_files:
    good_data = [False,False]
    cnv = pycnv.pycnv(f)

    try: # Check if we have pressure data
        p = cnv.data['p']
    except:
        continue
    
    try: # Check if we have data of sensor package 0
        SA00 = cnv.cdata['SA00']
        CT00 = cnv.cdata['CT00']    
        good_data[0] = True
        SA00_tmp = interp(p_int,p,SA00,left=NaN,right=NaN)
        CT00_tmp = interp(p_int,p,CT00,left=NaN,right=NaN)
        SA_unit = cnv.cunits['SA00']
        CT_unit = cnv.cunits['CT00']                
    except:
        SA00_tmp = p_int * NaN
        CT00_tmp = p_int * NaN

    try: # Check if we have data of sensor package 1
        SA11 = cnv.cdata['SA11']
        CT11 = cnv.cdata['CT11']    
        good_data[1] = True
        SA11_tmp = interp(p_int,p,SA11,left=NaN,right=NaN)
        CT11_tmp = interp(p_int,p,CT11,left=NaN,right=NaN)
        SA_unit = cnv.cunits['SA11']
        CT_unit = cnv.cunits['CT11']

    except:
        SA11_tmp = p_int * NaN
        CT11_tmp = p_int * NaN

    
    if(good_data[0] or good_data[1]):
        lon_all.append(cnv.lon)
        lat_all.append(cnv.lat)
        date_all.append(cnv.date)
        tn = netCDF4.date2num(cnv.date,timenum_unit)
        timenum_all.append(tn)
        SA00_int.append(SA00_tmp)
        CT00_int.append(CT00_tmp)
        SA11_int.append(SA11_tmp)
        CT11_int.append(CT11_tmp)


lon_all = asarray(lon_all)
lat_all = asarray(lat_all)
date_all = asarray(date_all)
timenum_all = asarray(timenum_all)
SA00_int = asarray(SA00_int)
CT00_int = asarray(CT00_int)
SA11_int = asarray(SA11_int)
CT11_int = asarray(CT11_int)
SA00_int = ma.masked_invalid(SA00_int)
CT00_int = ma.masked_invalid(CT00_int)
SA00_int = ma.masked_invalid(SA00_int)
CT11_int = ma.masked_invalid(CT11_int)

print('Creating the netCDF file with the interpolated data')
nc = netCDF4.Dataset('TF0271.nc','w')
nc.disclaimer = 'Example netCDF file showing the usage of the pycnv (' + pycnv.__version__ + ') package ' 
ncdim_t = nc.createDimension('time',None)
ncdim_p = nc.createDimension('p',len(p_int))

ncvar_t    = nc.createVariable('time','float',('time'))
ncvar_t.units = timenum_unit
ncvar_p    = nc.createVariable('p','float',('p'))
ncvar_p.units = 'dbar'
ncvar_lon  = nc.createVariable('lon', 'float',('time'))
ncvar_lat  = nc.createVariable('lat', 'float',('time'))                              
ncvar_SA00 = nc.createVariable('SA00','float',('time','p'))
ncvar_SA00.units = SA_unit
ncvar_CT00 = nc.createVariable('CT00','float',('time','p'))
ncvar_CT00.units = CT_unit
ncvar_SA11 = nc.createVariable('SA11','float',('time','p'))
ncvar_SA11.units = SA_unit
ncvar_CT11 = nc.createVariable('CT11','float',('time','p'))
ncvar_CT11.units = CT_unit

ncvar_t[:]   = timenum_all
ncvar_p[:]   = p_int
ncvar_lon[:] = lon_all
ncvar_lat[:] = lat_all
ncvar_SA00[:] = SA00_int
ncvar_CT00[:] = CT00_int
ncvar_SA11[:] = SA11_int
ncvar_CT11[:] = CT11_int
nc.close()
