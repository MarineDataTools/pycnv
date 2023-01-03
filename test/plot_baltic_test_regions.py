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
# Plot a map with the Baltic Sea regions
fig = pl.figure(1)
pl.clf()
ax = pl.axes([.1,.1,.8,.8],projection=ccrs.PlateCarree())
ax.set_extent([BAL_LON[0], BAL_LON[1], BAL_LAT[0], BAL_LAT[1]])
ax.coastlines('10m')
for i in range(len(regions_baltic)):
    lons = regions_baltic[i][0]
    lats = regions_baltic[i][1]    
    print(lons,lats)
    lonsb = [lons[0],lons[1],lons[1],lons[0],lons[0]]
    latsb = [lats[0],lats[0],lats[1],lats[1],lats[0]]    
    plb = ax.plot(lonsb,latsb,'-b')

pl.legend(plb,('Baltic test regions',))
pl.draw()

pl.savefig('./baltic_test_regions.pdf')
pl.show()
