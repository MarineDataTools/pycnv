#
# Script plots the regions used by the pycnv module to figure out if a
# CTD cast was performed in the Baltic Sea. This is necessary due to a
# slightly different absolute salinity formulation of the Baltic Sea
# water.
#
import pylab as pl
import pycnv
import cartopy.crs as ccrs

# Baltic
BAL_LON = [6.0,31.0]
BAL_LAT = [53.0,66.5]

regions_baltic = pycnv.regions_baltic
stations = pycnv.get_stations()
# Plot a map with the Baltic Sea regions
fig = pl.figure(1)
pl.clf()
ax = pl.axes([.1,.1,.8,.8],projection=ccrs.PlateCarree())
ax.set_extent([BAL_LON[0], BAL_LON[1], BAL_LAT[0], BAL_LAT[1]])
ax.coastlines('10m')
for i in range(len(stations)):
    lons = stations[i]['longitude']
    lats = stations[i]['latitude']
    print(lons,lats)
    plb = ax.plot(lons,lats,'.k')
    plt = ax.text(lons,lats,stations[i]['name'])


pl.savefig('./baltic_stations.pdf')
pl.show()
