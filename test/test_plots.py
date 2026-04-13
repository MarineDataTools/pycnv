import pytest
import pycnv

import matplotlib.pyplot as pl
import cartopy.crs as ccrs


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


def test_regions_baltic_exact():
    expected = [
        [[10.2, 13.0], [56.2, 57.5]],
        [[9.4, 13.4], [53.9, 56.3]],
        [[13.3, 17.0], [53.4, 56.3]],
        [[15.9, 24.6], [54.2, 60.2]],
        [[24.3, 30.4], [59.1, 60.8]],
        [[16.8, 23.3], [60.1, 63.3]],
        [[18.8, 25.6], [63.1, 66.2]],
    ]
    assert len(pycnv.regions_baltic) == len(expected)
    for actual_region, expected_region in zip(pycnv.regions_baltic, expected):
        assert actual_region[0] == pytest.approx(expected_region[0])
        assert actual_region[1] == pytest.approx(expected_region[1])
