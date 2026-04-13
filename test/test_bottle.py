import math
import pytest
from pathlib import Path

import numpy
import gsw

from pycnv import parse_time


class Bottle:
    def __init__(self, filename):
        self.filename = filename
        self.header = None
        self.start_date = None
        self.nmea_date = None
        self.lon = numpy.nan
        self.lat = numpy.nan
        self.data = None

        f = open(filename)
        ll = f.readlines()
        f.close()

        # separate header from data table (with column names still)
        head_lines = [
            l.replace("\n", "") for l in ll if l.startswith("*") or l.startswith("#")
        ]
        data_lines = ll[len(head_lines) :]

        self.header = head_lines
        self._parse_header()

        self._parse_data(data_lines)

    def _parse_header(self):
        """
        Parses the header of the btl file
        """

        # make educated guess for 'delimiter' of custom header items ('**')
        # will try "=" or ":"
        custom_delim = "="
        try:
            custom_header_lines = [l for l in self.header if "**" in l and l != "**"]
            ncust = len(custom_header_lines)
            ncounted = "".join(custom_header_lines).count(custom_delim)

            if ncounted < ncust:
                custom_delim = ":"

                custom_header_lines = [
                    l for l in self.header if "**" in l and l != "**"
                ]
                ncust = len(custom_header_lines)
                ncounted = "".join(custom_header_lines).count(custom_delim)

                if ncounted < ncust:
                    print(
                        "warning, could not find seabird metadata delimiter, will use '='"
                    )

        except:
            print("warning, used '=' as delimiter for custom seabird meta data ('**')")

        for l in self.header:
            if ("* NMEA Latitude" in l) or ("* NMEA Longitude" in l):
                pos_str = l.rsplit("=")[1]
                pos_str = pos_str.replace("\n", "").replace("\r", "")
                SIGN = numpy.nan
                if "S" in pos_str:
                    SIGN = -1.0
                if "N" in pos_str:
                    SIGN = 1.0
                if "W" in pos_str:
                    SIGN = -1.0
                if "E" in pos_str:
                    SIGN = 1.0

                pos_str = pos_str.replace("  ", " ")
                while pos_str[0] == " ":
                    pos_str = pos_str[1:]

                pos_str_deg = pos_str.split(" ")[0]
                pos_str_min = pos_str.split(" ")[1]

                pos = SIGN * (float(pos_str_deg) + float(pos_str_min) / 60.0)
                if "* NMEA Latitude" in l:
                    self.lat = pos
                if "* NMEA Longitude" in l:
                    self.lon = pos

            if "* NMEA UTC (Time) = " in l:
                line = l.split(" = ")
                line1 = line[1].split(" [")
                datum = line1[0]
                self.nmea_date = parse_time(datum)

            if "# start_time = " in l:
                line = l.split(" = ")
                line1 = line[1].split(" [")
                datum = line1[0]
                self.start_date = parse_time(datum)

            if "** " in l:  # User defined additional information
                try:
                    self.seabird_meta
                except:
                    self.seabird_meta = {}

                try:
                    splitted = l.split(custom_delim)
                    key = splitted[0][3:].strip()
                    if len(splitted) > 2:
                        data = custom_delim.join(splitted[1:]).strip()
                    else:
                        data = splitted[1].lstrip()
                    self.seabird_meta[key] = data
                except:
                    pass

    def _parse_data(self, data_lines):
        """
        Parses the data lines of the btl file. It was tested with data from two
        different platforms and likely needs adjustments, as some assumptions
        on the generic data structure were implicitly made.
        """

        # get column names
        data_cols1 = data_lines[0].split()
        data_cols2 = data_lines[1].split()  # assuming here are only 2 items

        # count occurences of "min", "max", "avg", "std" -> find number of data lines per bottle
        nmin = "".join(data_lines).count("min")
        nmax = "".join(data_lines).count("max")
        navg = "".join(data_lines).count("avg")
        nstv = "".join(data_lines).count("sdev")

        nline_per_btl = 0
        line_keys = []

        if navg > 0:
            nline_per_btl = 1
            line_keys += ["avg"]
            if navg == nstv:
                nline_per_btl += 1
                line_keys += ["sdev"]
            if navg == nmin:
                nline_per_btl += 1
                line_keys += ["min"]
            if navg == nmax:
                nline_per_btl += 1
                line_keys += ["max"]
        else:
            print(".. unknown file formatting ('avg' not available)")

        # test (assuming column 'header' consists of two lines) if number of lines is
        # a multiple of the previously determined 'nline_per_btl'
        try:
            nline_per_btl_ = int((len(data_lines) - 2) / navg)
            if nline_per_btl != nline_per_btl_:
                print(
                    ".. unknown file formatting (wrt number of data lines per bottle)"
                )
        except:
            print(
                ".. unknown file formatting (wrt number of data lines per bottle or number of headerlines used for column names)"
            )

        # parse date and time information (should be in first two lines)
        b_date = [" ".join(l.split()[1:4]) for l in data_lines[2::nline_per_btl]]

        # sanity check 1: try parse_time(b_date[0]+" 0:0:0")
        try:
            parse_time(b_date[0] + " 0:0:0")
        except:
            print(".. failed to parse b_date")

        # sanity check 2: check if second line of data contains a string with ":" in first or second position
        time_is_first = ":" in data_lines[3].split()[0]
        time_is_second = ":" in data_lines[3].split()[1]

        if time_is_first or time_is_second:
            b_time = [
                l.split()[int(time_is_second)] for l in data_lines[3::nline_per_btl]
            ]
        else:
            print(".. unknown data formatting (in row containing time)")

        try:
            b_datetime = [
                parse_time(b_date[ii] + " " + b_time[ii])
                for ii in numpy.arange(len(b_date))
            ]
        except:
            print("time parsing failed")

        # step 3: parse data, finally

        # brute-force bug fix for non-separated 'FlECO-AFLTurbWETntu0' in IOW example files
        items_fleco = [f for f in data_cols1 if "FlECO-AFL" in f]
        if len(items_fleco) > 0:
            for item_fleco in items_fleco:
                if len(item_fleco) > len("FlECO-AFL"):
                    data_cols1.remove(item_fleco)

                    i_item = item_fleco.find("FlECO-AFL")
                    data_cols1 += [
                        item_fleco[i_item : i_item + len("FlECO-AFL")],
                        item_fleco[i_item + len("FlECO-AFL") :],
                    ]

        ndatacol = (
            len(data_cols1) - 2
        )  # number of variables (excludingtime stamp and bottle numbers)

        data_lines = data_lines[2:]

        data_array = numpy.array(
            [l.split()[-ndatacol - 1 : -1] for l in data_lines]
        ).astype(float)
        type_list = [
            l.split()[-1].replace("(", "").replace(")", "") for l in data_lines
        ][:nline_per_btl]

        # put values in dictionary like data["T090C"]["avg"] for now
        data = {}

        for var_key in data_cols1[2:]:
            data[var_key] = {}
            i_col = data_cols1[2:].index(var_key)

            for line_key in line_keys:
                line_key_ind = type_list.index(line_key)

                data[var_key][line_key] = data_array[line_key_ind::nline_per_btl, i_col]

        # add variable in first position of second row (before 'time', 'Btl_ID' in IOW example, empty for AWI example)
        if time_is_second:
            data[data_cols2[0]] = [l.split()[0] for l in data_lines[1::nline_per_btl]]

        data[data_cols1[0]] = [l.split()[0] for l in data_lines[::nline_per_btl]]

        # compute depth from pressure
        try:
            depth = -gsw.z_from_p(data["PrDM"], self.lat)
            data["depth"] = depth
        except:
            pass

        data["time"] = b_datetime
        # self.time = b_datetime
        self.data = data
        self.names = data.keys()


BTL_DIR = Path(__file__).parent / "bottlefile_test_data"

# Expected values extracted from static test data files (n_bottles, T[0], p[0], T[-1], p[-1])
BTL_EXPECTED = {
    "V0001F02.btl": (13, 3.4229, 10.2810, 6.9138, 234.4310),
    "V0020F02.btl": (6, 2.3932, 10.3780, 5.6599, 58.5530),
    "V0021F02.btl": (14, 2.5558, 10.3770, 6.1831, 92.6630),
    "V0022F01.btl": (12, 2.5724, 10.4120, 6.2893, 117.4330),
    "V0023F02.btl": (13, 2.7795, 10.3650, 6.6717, 140.5600),
    "V0024F01.btl": (13, 2.9059, 10.3740, 6.4669, 106.8050),
    "V0025F01.btl": (12, 2.4514, 10.3540, 6.3451, 116.8530),
    "V0026F01.btl": (12, 2.5923, 10.3620, 6.1610, 113.9620),
    "V0027F01.btl": (10, 2.4276, 10.3240, 5.9279, 92.6810),
    "V0028F01.btl": (6, 2.3314, 10.3390, 5.2398, 58.0350),
    "V0029F01.btl": (5, 2.0944, 10.3450, 2.9502, 51.0010),
    "V0030F01.btl": (5, 6.4712, 106.4200, 6.4728, 106.4510),
}

BTL_FILES = sorted(BTL_DIR.glob("*.btl"))


@pytest.mark.parametrize("btl_file", BTL_FILES, ids=[f.name for f in BTL_FILES])
def test_bottle_parses(btl_file):
    b = Bottle(str(btl_file))
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
    assert T[0] == pytest.approx(T0, abs=1e-3)
    assert p[0] == pytest.approx(p0, abs=1e-3)
    assert T[-1] == pytest.approx(Tn, abs=1e-3)
    assert p[-1] == pytest.approx(pn, abs=1e-3)


def test_bottle_v0001f02_values(btl_dir):
    b = Bottle(str(btl_dir / "V0001F02.btl"))
    assert b.lat == pytest.approx(57.3195, abs=1e-3)
    assert b.lon == pytest.approx(20.0495, abs=1e-3)
    assert b.seabird_meta["ReiseNr"].strip() == "EMB-177"
    assert b.start_date is not None
    assert b.start_date.tzinfo is not None
