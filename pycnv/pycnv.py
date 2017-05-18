import datetime
from pytz import timezone
from numpy import *
import logging
import sys
import argparse
import yaml
    

# TODO: add NMEA position, time

# Setup logging module
logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
logger = logging.getLogger('pycnv2')


try:
    import gsw
except:
    logger.warning('Could not install the Gibbs Seawater toolbox')



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



class pycnv2(object):
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
    def __init__(self,filename, only_metadata = False,verbosity = logging.INFO):
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
        # Trying to extract standard names (p,C,S,T,oxy ... ) from the channel names
        self.
        
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
                titles.append('c' + str(n))

            print(names)
            self.data = zeros(shape(self.raw_data)[0],dtype={'names':names,'formats':formats,'titles':titles})
            for n,c in enumerate(self.channels):
                self.data[n] = self.raw_data[n,:]

            self.data = rec.array(self.data)
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
            # Look for sensor names and units of type:
            # # name 4 = t090C: Temperature [ITS-90, deg C]
            if "# name" in l:
                lsp = l.split("= ",1)
                sensor = {}
                sensor['index'] = int(lsp[0].split('name')[-1])
                sensor['name'] = lsp[1].split(': ')[0]
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
            
          
def test_pycnv2():
    pycnv2("/home/holterma/data/redox_drive/iow_data/fahrten.2011/06EZ1108.DTA/vCTD/DATA/cnv/0001_01.cnv")

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


pc = pycnv2("/home/holterma/data/redox_drive/iow_data/fahrten.2011/06EZ1108.DTA/vCTD/DATA/cnv/0001_01.cnv")
#if __name__ == '__main__':
#   # main()
#   pc = test_pycnv2()
    

