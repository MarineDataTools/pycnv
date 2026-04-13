import datetime
import pytest
import pycnv


def test_parse_time_basic():
    result = pycnv.parse_time("Feb 26 2018 08:31:55")
    assert isinstance(result, datetime.datetime)
    assert result.year == 2018
    assert result.month == 2
    assert result.day == 26
    assert result.hour == 8
    assert result.minute == 31
    assert result.second == 55
    assert result.tzinfo is not None


def test_parse_time_invalid_returns_none():
    result = pycnv.parse_time("not a date")
    assert result is None


def test_check_baltic_inside():
    # Central Baltic (Bornholm basin area)
    assert pycnv.check_baltic(17.0, 55.0) is True


def test_check_baltic_outside():
    # North Sea
    assert pycnv.check_baltic(3.0, 55.0) is False
    # North Atlantic
    assert pycnv.check_baltic(-10.0, 50.0) is False


def test_get_stations_returns_list():
    stations = pycnv.get_stations()
    assert isinstance(stations, list)
    assert len(stations) > 0


def test_get_stations_keys():
    stations = pycnv.get_stations()
    for s in stations:
        assert "name" in s
        assert "longitude" in s
        assert "latitude" in s


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
