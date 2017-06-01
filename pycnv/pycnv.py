import datetime
from pytz import timezone
from numpy import *
import logging
import sys
import argparse
import pkg_resources
import yaml

standard_name_file = pkg_resources.resource_filename('pycnv', 'rules/standard_names.yaml')    

# TODO: add NMEA position, time

# Setup logging module
logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
logger = logging.getLogger('pycnv')


try:
    import gsw
except:
    logger.warning('Could not load the Gibbs Seawater toolbox')



def date_correction(tag, monat, jahr):
    """
    @author: Robert Mars, IOW
    modified and improved by Peter Holtermann, IOW
    """
    
    ### Vereinheitlichung des Datums nach ISO
    # German month naming
    if monat.lower()=="dez": monat_int = 12
    if monat.lower()=="mrz": monat_int = 5        
    if monat.lower()=="mai": monat_int = 5
    if monat.lower()=="okt": monat_int = 10    
    if monat.lower()=="jan": monat_int = 1
    if monat.lower()=="feb": monat_int = 2
    if monat.lower()=="mar": monat_int = 3
    if monat.lower()=="apr": monat_int = 4
    if monat.lower()=="may": monat_int = 5
    if monat.lower()=="jun" :monat_int = 6
    if monat.lower()=="jul": monat_int = 7
    if monat.lower()=="aug": monat_int = 8
    if monat.lower()=="sep": monat_int = 9
    if monat.lower()=="oct": monat_int = 10
    if monat.lower()=="nov": monat_int = 11
    if monat.lower()=="dec": monat_int = 12

    # print ("day: %s| month: %s| year: %s " % (cal[0],cal[1],cal[2]))
    # print ("date: %s" % datetime.date(cal_year,cal_month,cal_day))
    try:
        datstr = datetime.date(int(jahr),int(monat_int),int(tag)).isoformat()
        return datstr
    except Exception as e:
        logger.warning(' Could not convert date: ' + str(e))
        return None    


def parse_iow_header(header):
    """
    Parsing the header for iow_data and saving it into a structure
    """
    iow_data = {}
    for line in header.splitlines():
        #print line
        if  "Startzeit" in line:
            # ** Startzeit= 13:13:15 25-Sep-07
            line_orig = line
            #print(line)
            try:
                line = line.replace("\n","").replace("\r","")
                line = line.split("=")     
                line = line[1]
                line = line.replace("  "," ")
                while(line[0] == " "):
                    line = line[1:]

                line_split = line.split(" ")
                # Get datum
                datum_split = line_split[1].split("-")
                tag = datum_split[0]
                monat = datum_split[1]            
                jahr = datum_split[2]
                if(len(jahr) == 2):
                    jahr = '20' + jahr

                #print(line)
                datum_start = date_correction(tag, monat, jahr)


                # get time
                zeit_start = line_split[0]
                try:
                    iow_data['date'] = datetime.datetime.strptime(datum_start + zeit_start,'%Y-%m-%d%H:%M:%S')
                    iow_data['date'].replace(tzinfo=timezone('UTC'))
                except:
                    iow_data['date'] = None                        
            except Exception as e:
                logger.warning('Startzeit parsing error:' + str(e))
                logger.warning('Startzeit str:' + line_orig)

        ###### Meta-Daten der Reise und Station
        elif "ReiseNr" in line:
            line = line.split("=")
            reise = line[1]
            reise = reise.replace(" ","")
            reise = reise.replace("\n","").replace("\r","")
            iow_data['reise'] = reise
            # print("Reise: %s" % reise)
        elif "StatBez" in line:
            line = line.split("=")
            station_bez = line[1]
            # station_bez = station_bez.replace(" ","")
            station_bez = station_bez.replace("\n","").replace("\r","")
            iow_data['station'] = station_bez
            # print("Station: %s" % station_bez)
        elif "EinsatzNr" in line:
            line = line.split("=")
            einsatz_nr = line[1]
            einsatz_nr = einsatz_nr.replace(" ","")
            einsatz_nr = einsatz_nr.replace("\n","").replace("\r","")
            iow_data['einsatz'] = einsatz_nr
            # print("Einsatz: %s" % einsatz_nr)

        elif "Echolote" in line:

            line = line.split("=")
            try:
                echo0 = float(line[1].split('m')[0])
            except Exception as e:
                logger.warning('IOW:Echolot:' + str(e))
                echo0 = None

            try:
                echo1 = float(line[1].split('m')[1])
            except Exception as e:
                logger.warning('IOW:Echolot:' + str(e))
                echo1 = None                

            iow_data['echo'] = (echo0,echo1)
                
            # print("Einsatz: %s" % einsatz_nr)            
        elif "SerieNr" in line and "Operator" in line:
            line_orig = line
            line.replace("\n","").replace("\r","")
            line = line.split()
            try:
                serie_nr = line[3]
            except Exception as e:
                logger.warning('SerieNr parsing error:' + str(e))
                logger.warning('str:' + line_orig)

            try:                
                operator = line[5]
            except Exception as e:
                logger.warning('Operator parsing error:' + str(e))
                logger.warning('str:' + line_orig)

            # print("Serie: %s" % serie_nr)
            # print("Operator: %s" % operator)
            iow_data['serie'] = serie_nr
            iow_data['operator'] = operator
        elif "GPS_Posn" in line:
            try:

                pos_str = line.rsplit('=')[1]
                pos_str = pos_str.replace("\n","").replace("\r","") 
                if("S" in pos_str):
                    SIGN_NORTH = -1.
                    CHAR_NORTH = 'S'
                if("N" in pos_str):
                    SIGN_NORTH = 1.
                    CHAR_NORTH = 'N'                

                if("E" in pos_str):
                    SIGN_WEST = 1.0
                    CHAR_WEST = 'E'
                if("W" in pos_str):
                    SIGN_WEST = -1.0
                    CHAR_WEST = 'W'

                pos_str = pos_str.replace("N","")
                pos_str = pos_str.replace("S","")
                pos_str = pos_str.replace("E","")
                pos_str = pos_str.replace("W","")
                pos_str = pos_str.replace("  "," ")
                pos_str = pos_str.split()
                while(pos_str[0] == " "):
                        pos_str = pos_str[1:]


                latitude = ("%s %s" % (pos_str[0],pos_str[1]))
                longitude = ("%s %s" % (pos_str[2],pos_str[3]))
                latitude += CHAR_NORTH
                longitude += CHAR_WEST
                # Convert to floats
                lon = SIGN_WEST * float(longitude.split()[0]) + float(longitude.split()[1][:-1])/60.
                lat = SIGN_NORTH * float(latitude.split()[0]) + float(latitude.split()[1][:-1])/60.

            except Exception as e:
                logger.warning('Could not get a valid position, setting it to unknown:' + str(e))
                logger.warning('str:' + line)
                logger.warning('pos str:' + str(pos_str))
                latitude = 'unknown'
                longitude = 'unknown'
                lat = NaN
                lon = NaN
                
            iow_data['lat'] = lat
            iow_data['lon'] = lon

    return iow_data


class pycnv(object):
    """

    A Seabird cnv parsing object.

    Author: Peter Holtermann (peter.holtermann@io-warnemuende.de)

    Usage:
       >>>filename='test.cnv'
       >>>cnv = pycnv(filename)
       >>># Derive absolute salinity and conservative temperature from in situ temperature and conductivity
       >>>cnv.derive('ST')
       >>>plot(cnv.derived['SA00']
    
    """
    def __init__(self,filename, only_metadata = False,verbosity = logging.INFO, naming_rules = standard_name_file ):
        """
        """
        logger.setLevel(verbosity)
        logger.info(' Opening file: ' + filename)
        self.filename = filename
        self.channels = []     
        # Opening file for read
        raw = open(self.filename, "r")
        # Find the header and store it
        header = self.get_header(raw)
        self.parse_header()
        # Custom header information
        self.iow = parse_iow_header(self.header)
        self.lat = self.iow['lat']
        self.lon = self.iow['lon']
        # Trying to extract standard names (p, C, S, T, oxy ... ) from the channel names
        self.get_standard_channel_names(naming_rules)
        
        self.get_data(raw)

        # Check if the dimensions are right
        if( shape(self.raw_data)[1] == len(self.channels) ):
            # Make a recarray out of the array
            names   = []
            formats = []
            titles  = []
            # Name the columns after the channel names
            for n,c in enumerate(self.channels):
                names.append(c['name'])
                formats.append('float')
                titles.append(c['title'])

            # Create a new recarray with the names as in the header as
            # the name and the standard names as the title
            self.data = zeros(shape(self.raw_data)[0],dtype={'names':names,'formats':formats,'titles':titles})
            # Fill the recarray
            for n,c in enumerate(self.channels):
                self.data[n] = self.raw_data[n,:]

            self.data = rec.array(self.data)
            # Compute density with the gsw toolbox
            
        else:
            logger.warning('Different number of columns in data section as defined in header, this is bad ...')

        
    def get_header(self,raw):
        """
        Loops through lines and looks for header. It removes all \r leaving only \n for newline and saves the header in self.header as a string
        Args:
        Return:
            Line number of first data 
        """
        self.header = ''
        # Read line by line
        nline = 0
        for l in raw:
            nline +=1
            # removes all "\r", we only want "\n"
            l = l.replace("\r","")
            self.header += l
            if("*END*" in l):
                break
            # Check if we read more than 10000 lines and found nothing
            if(nline > 10000):
                self.header = ''
                break

        return nline

    def parse_header(self):
        """
        Parses the header of the cnv file
        """
        for l in self.header.split('\n'):
            if "System UpLoad Time" in l:
                line     = l.split(" = ")
                datum = line[1]
                try:
                    self.date = datetime.datetime.strptime(datum,'%b %d %Y %H:%M:%S')
                    self.date.replace(tzinfo=timezone('UTC'))
                except Exception as e:
                    logger.warning('Could not decode time:' + str(e))
                    self.date = None

            # Look for sensor names and units of type:
            # # name 4 = t090C: Temperature [ITS-90, deg C]
            if "# name" in l:
                lsp = l.split("= ",1)
                sensor = {}
                sensor['index'] = int(lsp[0].split('name')[-1])
                sensor['name'] = lsp[1].split(': ')[0]
                sensor['title'] = 'i' + str(sensor['index'])
                sensor['long_name'] = lsp[1].split(': ')[1]
                unit = lsp[1].split(': ')[1]
                if len(unit.split('[')) > 1 :
                    unit = unit.split('[')[1]
                    unit = unit.split("]")[0]
                    sensor['unit'] = unit
                else:
                    sensor['unit'] = None

                self.channels.append(sensor)
        
        
    def get_standard_channel_names(self, naming_rules):
        """
        Look through a list of rules to try to link names to standard names
        """
        f = open(naming_rules)
        rules = yaml.safe_load(f)
        print('Hallo!')
        found = False
        for r in rules['names']:
            logger.debug('Looking for rule for ' + r['description'])
            for c in r['channels']:
                if(found == True):
                    found = False
                    break
                for ct in self.channels:
                    if(ct['name'] in c):
                        ct['title'] = r['name']
                        print('Found channel',ct,c)
                        found = True
                        break
    
        
        #print('Channels',self.channels)
        
    def get_data(self,raw):
        """
        Reads until the end of the file lines of data and puts them into one big numpy array
        """
        data = []
        nline = 0
        for l in raw:
            line_orig = l
            l = l.replace("\n","").replace("\r","")
            l = l.split()
            #data.append (line)
            nline += 1
            try:
                ldata = asarray(l,dtype='float')
                # Get the number of columns with the first line
                if(nline == 1):
                    ncols = len(ldata)

                if(len(ldata) == ncols):
                    data.append(ldata)
            except Exception as e:
                logger.warning('Could not convert data to floats in line:' + str(nl))
                logger.debug('str:' + line_orig)

            
        self.raw_data = asarray(data)

    def get_summary(self,header=False):
        """
        Returns a summary of the cnv file in a csv format
        Args:
           header: Returns header only
        """
        
        sep = ','
        rstr = ""        
        if(header):
            rstr += 'Date,'
            rstr += 'Lat,'
            rstr += 'Lon,'
            rstr += 'p min,'
            rstr += 'p max,'
            rstr += 'num p samples,'            
            rstr += 'file,'            
        else:
            try:
                rstr += datetime.datetime.strftime(self.date,'%Y-%m-%d %H:%M:%S') + sep
            except: 
                rstr += 'NaN' + sep
            rstr += str(self.lat) + sep
            rstr += str(self.lon) + sep
            pmin = NaN
            pmax = NaN
            num_samples = NaN                    
            if(self.data != None):
                #print(self.data)
                try:
                    pmin = self.data['p'].min()
                    pmax = self.data['p'].max()
                    num_samples = len(self.data['p'])
                except Exception as e:
                    pass

                                 
            rstr += str(pmin) + sep
            rstr += str(pmax) + sep
            rstr += str(num_samples) + sep                
            rstr += self.filename + sep
                
        return rstr


    def __str__(self):
        """
        String format
        """
        rstr = ""
        rstr += "pycnv of " + self.filename
        rstr += " at Lat: " + str(self.header['lat'])
        rstr += ", Lon: " + str(self.header['lon'])
        rstr += ", Date: " + datetime.datetime.strftime(self.header['date'],'%Y-%m-%d %H:%M:%S')
        return rstr        
            
          
def test_pycnv():
    pycnv("/home/holterma/data/redox_drive/iow_data/fahrten.2011/06EZ1108.DTA/vCTD/DATA/cnv/0001_01.cnv")

# Main function
def main():
    sum_help = 'Gives a csv compatible summary'
    sumhead_help = 'Gives the header to the csv compatible summary'
    parser = argparse.ArgumentParser()
    parser.add_argument('--filename', '-f')    
    parser.add_argument('--summary', '-s', action='store_true', help=sum_help)
    parser.add_argument('--summary_header', '-sh', action='store_true', help=sumhead_help)
    parser.add_argument('--verbose', '-v', action='count')
    args = parser.parse_args()
    
    if(args.verbose == None):
        loglevel = logging.CRITICAL
    elif(args.verbose == 1):
        loglevel = logging.WARNING
    elif(args.verbose == 2):
        loglevel = logging.INFO        
    elif(args.verbose > 2):
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO


    logger.setLevel(loglevel)
    
    filename = args.filename

    print_summary = args.summary
    print_summary_header = args.summary_header
    
    if(filename != None):
        cnv = pycnv(filename,verbosity=loglevel)
        #print(cnv.data)
    else:
        logger.critical('Need a filename')

    if(print_summary_header):
        summary = cnv.get_summary(header=True)
        print(summary)
    if(print_summary):
        summary = cnv.get_summary()
        print(summary)


pc = pycnv("/home/holterma/data/redox_drive/iow_data/fahrten.2011/06EZ1108.DTA/vCTD/DATA/cnv/0001_01.cnv")
#if __name__ == '__main__':
#   # main()
#   pc = test_pycnv()
    

