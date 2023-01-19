
import numpy
import gsw

from pycnv import parse_time

class bottle(object):
    def __init__(self, filename):

        self.filename        = filename

        self.header          = None

        self.start_date      = None
        self.nmea_date       = None   
        
        self.lon             = numpy.nan
        self.lat             = numpy.nan

        self.data            = None
 
        
        f = open(filename)
        ll = f.readlines()
        f.close()
        
        # separate header from data table (with column names still)
        head_lines = [l.replace("\n","") for l in ll if l.startswith("*") or l.startswith("#")]
        data_lines = ll[len(head_lines):]

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
        
                custom_header_lines = [l for l in self.header if "**" in l and l != "**"]
                ncust = len(custom_header_lines)
                ncounted = "".join(custom_header_lines).count(custom_delim)
                
                if ncounted < ncust:
                    print("warning, could not find seabird metadata delimiter, will use '='")
        
        except:
            print("warning, used '=' as delimiter for custom seabird meta data ('**')")
        
        
        for l in self.header:

            if("* NMEA Latitude" in l) or ("* NMEA Longitude" in l):
                pos_str = l.rsplit('=')[1]
                pos_str = pos_str.replace("\n","").replace("\r","")
                SIGN = numpy.NaN
                if("S" in pos_str):
                    SIGN = -1.
                if("N" in pos_str):
                    SIGN = 1.
                if("W" in pos_str):
                    SIGN = -1.
                if("E" in pos_str):
                    SIGN = 1.

                pos_str = pos_str.replace("  "," ")
                while(pos_str[0] == " "):
                    pos_str = pos_str[1:]                    

                pos_str_deg = pos_str.split(" ")[0]
                pos_str_min = pos_str.split(" ")[1]

                pos = SIGN * (float(pos_str_deg) + float(pos_str_min)/60.)
                if("* NMEA Latitude" in l):
                    self.lat = pos
                if("* NMEA Longitude" in l):
                    self.lon = pos

            if "* NMEA UTC (Time) = " in l:
                line     = l.split(" = ")
                line1     = line[1].split(" [")                
                datum = line1[0]
                self.nmea_date = parse_time(datum)

                    
            if "# start_time = " in l:
                line     = l.split(" = ")
                line1     = line[1].split(" [")                
                datum = line1[0]
                self.start_date = parse_time(datum)


            if "** " in l: # User defined additional information
            
                try:
                    self.seabird_meta
                except:
                    self.seabird_meta = {}
                
                try:
                    splitted = l.split(custom_delim)
                    key = splitted[0][3:].strip()
                    if len(splitted)>2:
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
            nline_per_btl  = 1
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
            nline_per_btl_ = int((len(data_lines)-2) / navg)
            if nline_per_btl!=nline_per_btl_:
                print(".. unknown file formatting (wrt number of data lines per bottle)")
        except:
            print(".. unknown file formatting (wrt number of data lines per bottle or number of headerlines used for column names)")
                
        
            
        # parse date and time information (should be in first two lines)        
        b_date = [ " ".join(l.split()[1:4]) for l in data_lines[2::nline_per_btl]]
        
        # sanity check 1: try parse_time(b_date[0]+" 0:0:0") 
        try:
            parse_time(b_date[0]+" 0:0:0")
        except:
            print(".. failed to parse b_date")    
        
        # sanity check 2: check if second line of data contains a string with ":" in first or second position
        time_is_first  =  ":" in data_lines[3].split()[0]
        time_is_second =  ":" in data_lines[3].split()[1]
        
        if time_is_first or time_is_second:
            b_time = [ l.split()[int(time_is_second)] for l in data_lines[3::nline_per_btl]]
        else:
            print(".. unknown data formatting (in row containing time)")
            
            
        try:
            b_datetime = [parse_time(b_date[ii] +" "+ b_time[ii]) for ii in numpy.arange(len(b_date))]
        except:
            print("time parsing failed")
        

        # step 3: parse data, finally
        
        # brute-force bug fix for non-separated 'FlECO-AFLTurbWETntu0' in IOW example files
        items_fleco = [f for f in data_cols1 if "FlECO-AFL" in f]
        if len(items_fleco)>0:
            for item_fleco in items_fleco:
                if len(item_fleco) > len("FlECO-AFL"):
                    data_cols1.remove(item_fleco)
                    
                    i_item = item_fleco.find("FlECO-AFL")
                    data_cols1+= [item_fleco[i_item:i_item+len("FlECO-AFL")] , item_fleco[i_item+len("FlECO-AFL"):]]
                
        
        ndatacol = len(data_cols1)-2 # number of variables (excludingtime stamp and bottle numbers)
        
        data_lines = data_lines[2:]
        
        data_array  = numpy.array([l.split()[-ndatacol-1:-1] for l in data_lines ]).astype(float)
        type_list   = [l.split()[-1].replace("(","").replace(")","") for l in data_lines][:nline_per_btl]
        
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
        
        
        

    
#%% plot all temperature profiles from example files

import matplotlib.pyplot as plt
import os

fp_test = "bottlefile_test_data/"


for fn in [f for f in os.listdir(fp_test) if f.endswith("btl")]:
# if True:
    filename = fp_test+fn
    
    btl = bottle(filename)
        
    T = btl.data["T090C"]["avg"]    
    p = btl.data["PrDM"]["avg"]
    
    plt.plot(T, p, marker=".")
    
    
plt.gca().invert_yaxis()


print(btl.names)

print(btl.seabird_meta)


