import pytest
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as pl

cartopy = pytest.importorskip("cartopy")
import cartopy.crs as ccrs

import pycnv


def test_plot_baltic_test_regions():
    BAL_LON = [6.0, 31.0]
    BAL_LAT = [53.0, 66.5]

    fig = pl.figure()
    ax = fig.add_axes([0.1, 0.1, 0.8, 0.8], projection=ccrs.PlateCarree())
    ax.set_extent([BAL_LON[0], BAL_LON[1], BAL_LAT[0], BAL_LAT[1]])
    ax.coastlines("10m")
    for region in pycnv.regions_baltic:
        lons = region[0]
        lats = region[1]
        lonsb = [lons[0], lons[1], lons[1], lons[0], lons[0]]
        latsb = [lats[0], lats[0], lats[1], lats[1], lats[0]]
        ax.plot(lonsb, latsb, "-b")
    pl.close(fig)


def test_plot_baltic_stations():
    BAL_LON = [6.0, 31.0]
    BAL_LAT = [53.0, 66.5]

    stations = pycnv.get_stations()
    assert len(stations) > 0

    fig = pl.figure()
    ax = fig.add_axes([0.1, 0.1, 0.8, 0.8], projection=ccrs.PlateCarree())
    ax.set_extent([BAL_LON[0], BAL_LON[1], BAL_LAT[0], BAL_LAT[1]])
    ax.coastlines("10m")
    for s in stations:
        ax.plot(s["longitude"], s["latitude"], ".k")
        ax.text(s["longitude"], s["latitude"], s["name"])
    pl.close(fig)
