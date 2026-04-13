import sys
import pathlib
import math
import pytest

# Import the bottle class from the existing example script without moving it
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from bottle_example import bottle


BTL_DIR = pathlib.Path(__file__).parent / "bottlefile_test_data"

# Expected values extracted from static test data files (n_bottles, T[0], p[0], T[-1], p[-1])
BTL_EXPECTED = {
    "V0001F02.btl": (13, 3.4229,  10.2810, 6.9138, 234.4310),
    "V0020F02.btl": ( 6, 2.3932,  10.3780, 5.6599,  58.5530),
    "V0021F02.btl": (14, 2.5558,  10.3770, 6.1831,  92.6630),
    "V0022F01.btl": (12, 2.5724,  10.4120, 6.2893, 117.4330),
    "V0023F02.btl": (13, 2.7795,  10.3650, 6.6717, 140.5600),
    "V0024F01.btl": (13, 2.9059,  10.3740, 6.4669, 106.8050),
    "V0025F01.btl": (12, 2.4514,  10.3540, 6.3451, 116.8530),
    "V0026F01.btl": (12, 2.5923,  10.3620, 6.1610, 113.9620),
    "V0027F01.btl": (10, 2.4276,  10.3240, 5.9279,  92.6810),
    "V0028F01.btl": ( 6, 2.3314,  10.3390, 5.2398,  58.0350),
    "V0029F01.btl": ( 5, 2.0944,  10.3450, 2.9502,  51.0010),
    "V0030F01.btl": ( 5, 6.4712, 106.4200, 6.4728, 106.4510),
}

BTL_FILES = sorted(BTL_DIR.glob("*.btl"))


@pytest.mark.parametrize("btl_file", BTL_FILES, ids=[f.name for f in BTL_FILES])
def test_bottle_parses(btl_file):
    b = bottle(str(btl_file))
    assert b.data is not None
    assert math.isfinite(b.lat)
    assert math.isfinite(b.lon)
    assert "T090C" in b.data
    assert "PrDM" in b.data

    T = b.data["T090C"]["avg"]
    p = b.data["PrDM"]["avg"]
    assert all(math.isfinite(v) for v in T)
    assert all(math.isfinite(v) for v in p)

    n_bottles, T0, p0, Tn, pn = BTL_EXPECTED[btl_file.name]
    assert len(T) == n_bottles
    assert T[0]  == pytest.approx(T0,  abs=1e-3)
    assert p[0]  == pytest.approx(p0,  abs=1e-3)
    assert T[-1] == pytest.approx(Tn,  abs=1e-3)
    assert p[-1] == pytest.approx(pn,  abs=1e-3)



def test_bottle_v0001f02_values(btl_dir):
    b = bottle(str(btl_dir / "V0001F02.btl"))
    assert b.lat == pytest.approx(57.3195, abs=1e-3)
    assert b.lon == pytest.approx(20.0495, abs=1e-3)
    assert b.seabird_meta["ReiseNr"].strip() == "EMB-177"
    assert b.start_date is not None
    assert b.start_date.tzinfo is not None
