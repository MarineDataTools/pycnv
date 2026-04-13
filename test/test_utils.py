import datetime
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
    assert str(result.tzinfo) == "UTC"


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

    # Might want to add bounds here? IDK...
    assert pycnv.check_baltic(-1000, -1000) is False


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
