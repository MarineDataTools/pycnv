import datetime
from pytz import timezone
import numpy
import logging
import sys
import argparse
import pkg_resources
import yaml
import pylab as pl
import os
import hashlib
import errno
import locale

standard_name_file = pkg_resources.resource_filename('pycnv', 'rules/standard_names.yaml')

# Get the version
version_file = pkg_resources.resource_filename('pycnv','VERSION')

with open(version_file) as version_f:
   version = version_f.read().strip()

# Setup logging module
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger('pycnv')

# Regions to test if we are in the Baltic Sea for different equation of state
regions_baltic = []
regions_baltic.append([[ 10.2,  13. ],[ 56.2,  57.5]])
regions_baltic.append([[  9.4,  13.4],[ 53.9,  56.3]])
regions_baltic.append([[ 13.3,  17.],[ 53.4,  56.3]])
regions_baltic.append([[ 15.9,  24.6],[ 54.2,  60.2 ]])
regions_baltic.append([[ 24.3,  30.4],[ 59.1,  60.8]])
regions_baltic.append([[ 16.8,  23.3],[ 60.1,  63.3]])
regions_baltic.append([[ 18.8,  25.6],[ 63.1,  66.2]])


def parse_time(datum):
    """
    Parses a time string and tries different locales
    Parameters
    ----------
    datum : str
        A date as a string.

    Returns
    -------
    start_date : datetime
        The parsed date as a datetime object.

    """
    loc = locale.getlocale()
    try:
        start_date = datetime.datetime.strptime(datum,'%b %d %Y %H:%M:%S')
        start_date = start_date.replace(tzinfo=timezone('UTC'))
    except Exception as e:
        start_date = None
        logger.warning('parse_header() start_time: Could not decode time: ( ' + datum + ' )' + str(e) + ' locale' + str(loc))
        
    if(start_date == None): # Try english
        
        locale.setlocale(locale.LC_ALL, 'C')
        locnew = locale.getlocale()
        try:
            start_date = datetime.datetime.strptime(datum,'%b %d %Y %H:%M:%S')
            start_date = start_date.replace(tzinfo=timezone('UTC'))
        except Exception as e:
            start_date = None
            logger.warning('parse_header() start_time: Could not decode time: ( ' + datum + ' )' + str(e) + ' locale' + str(locnew))
        
        # Restoring the original locale
        locale.setlocale(locale.LC_ALL, loc)
    return start_date                 


def check_baltic(lon,lat):
    """
    Functions checks if position with lon,lat is in the Baltic Sea
    Args:
       lon: Longitude
       lat: Latitude
    Returns:
       baltic: True: In Baltic, False: not in Baltic
    """
    if(lon == None or lon == numpy.NaN or lat == None or lat == numpy.NaN):
        return False
    
    for i in range(len(regions_baltic)):
        lonb = regions_baltic[i][0]
        latb = regions_baltic[i][1]
        if((lon > lonb[0]) and (lon < lonb[1])):
            if((lat > latb[0]) and (lat < latb[1])):
                return True

    return False


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
    if monat.lower()=="mrz": monat_int = 3        
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


def parse_iow_header(header,pycnv_object=None):
    """ Parsing the header for iow_data and saving it into a structure
    """
    iow_data = {}
    for line in header.splitlines():
        #print line
        if  "Startzeit" in line:
            # This can happen
            # ** Startzeit= 13:13:15 25-Sep-07
            # ** Startzeit= 07:13:09 utc 28-APR-99
            line_orig = line
            line = line.replace('UTC','')
            line = line.replace('utc','')            
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
                    if(int(jahr) < 80): # 2000 - 2079
                        jahr = '20' + jahr
                    else: # 1980-1999
                        jahr = '19' + jahr                    

                #print(line)
                datum_start = date_correction(tag, monat, jahr)


                # get time
                zeit_start = line_split[0]
                try:
                    iow_data['date'] = datetime.datetime.strptime(datum_start + zeit_start,'%Y-%m-%d%H:%M:%S')
                    iow_data['date'] = iow_data['date'].replace(tzinfo=timezone('UTC'))
                except Exception as e:
                    logger.warning('Startzeit to datetime:' + str(e))
                    logger.warning('Startzeit str:' + line_orig)                    
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
                logger.debug('IOW:Echolot:' + str(e))
                echo0 = None

            try:
                echo1 = float(line[1].split('m')[1])
            except Exception as e:
                logger.debug('IOW:Echolot:' + str(e))
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
                logger.debug('SerieNr parsing error:' + str(e))
                logger.debug('str:' + line_orig)
                serie_nr = ''

            try:                
                operator = line[5]
            except Exception as e:
                logger.debug('Operator parsing error:' + str(e))
                logger.debug('str:' + line_orig)
                operator = ''                

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

                lon_str_min = longitude.split()[1][:-1]
                lat_str_min = latitude.split()[1][:-1]
                # The old Reise has ',' as decimal seperator, replace it with '.'
                lon_str_min = lon_str_min.replace(',','.')
                lat_str_min = lat_str_min.replace(',','.')                
                # Convert to floats
                lon = SIGN_WEST * float(longitude.split()[0]) + float(lon_str_min)/60.
                lat = SIGN_NORTH * float(latitude.split()[0]) + float(lat_str_min)/60.

            except Exception as e:
                logger.warning('Could not get a valid position, setting it to unknown:' + str(e))
                logger.warning('str:' + line)
                logger.warning('pos str:' + str(pos_str))
                latitude = 'unknown'
                longitude = 'unknown'
                lat = numpy.NaN
                lon = numpy.NaN
                
            iow_data['lat'] = lat
            iow_data['lon'] = lon

    # Add the data to the calling object (pycnv object)
    if pycnv_object is not None:
        pycnv_object.iow = iow_data
        try:
            if not(numpy.isnan(iow_data['lat'])):
                pycnv_object.lat = iow_data['lat']
                pycnv_object.lon = iow_data['lon']
        except:
            pass
        
        # If no date was found, try the IOW date
        if pycnv_object.date == None:
            try:
                pycnv_object.date = iow_data['date']
            except:
                pass         

    # Returns all data also as a dictionary
    return iow_data


class pycnv(object):
    """

    A Seabird cnv parsing object.

    Author: Peter Holtermann (peter.holtermann@io-warnemuende.de)

    Usage:
       >>>filename='test.cnv'
       >>>cnv = pycnv(filename)

    Args:
       filename:
       only_metadata:
       verbosity:
       naming_rules:
       encoding:
       baltic: Flag if the cast was in the Baltic Sea. None: Automatic check based on parsed lat/lon and the regions definded in pycnv.regions_baltic, True: cast is in Baltic, False: cast is not in Baltic. If cast is in Baltic the gsw equation of state for the Baltic Sea will be used.
       header_parse: Function for parsing custom header information, will be called like so: header_parse(header_str, self), where self is the pycnv object. The function can thus create fields of the pycnv object. See parse_iow_header() as an example
    
    """
    def __init__(self,filename, only_metadata = False,verbosity = logging.INFO, naming_rules = standard_name_file,encoding='latin-1',baltic=None, header_parse = parse_iow_header,calc_sha1=True  ):
        """
        """
        logger.setLevel(verbosity)
        logger.info(' Opening file: ' + filename)
        self.parse_custom_header = header_parse
        self.filename = filename
        self.file_type = ''
        self.channels = []
        self.data        = None
        self.date        = None
        self.upload_date = None
        self.start_date  = None
        self.nmea_date   = None        
        self.lon = numpy.NaN
        self.lat = numpy.NaN

        # Plotting variables
        self.figures = []
        self.axes    = []        
        # Opening file for reading
        try:
            # Calculate a md5 hash
            if(calc_sha1):
               BLOCKSIZE = 65536
               hasher = hashlib.sha1()
               with open(self.filename, 'rb') as afile:
                   buf = afile.read(BLOCKSIZE)
                   while len(buf) > 0:
                      hasher.update(buf)
                      buf = afile.read(BLOCKSIZE)

               self.sha1 = hasher.hexdigest()
               afile.close()               
            else:
               self.sha1 = None
               
            # Opening for reading
            raw = open(self.filename, "r",encoding=encoding)
        except Exception as e:
            logger.critical('Could not open file:' + self.filename + ' (Exception: {:s})'.format(str(e)))
            self.valid_cnv = False
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)
            #return
        
        #print('Hallo!',raw)
        # Find the header and store it
        header = self._get_header(raw)
        self._parse_header()
        # Decide which timestamp to use for the date
        #NMEA UTC (Time)
        if(self.nmea_date is not None):
            self.date = self.nmea_date
        elif(self.start_date is not None):
            self.date = self.start_date                        
        elif(self.upload_date is not None):
            self.date = self.upload_date

            
        # Check if we found channels
        # If yes we have a valid cnv file
        if(len(self.channels) == 0):
            logger.critical('Did not find any channels in file: ' + filename + ', exiting (No cnv file?)')
            self.valid_cnv = False
            return

        # Check if we have a known data format
        if 'ASCII' in self.file_type.upper():
            pass
        else:
            logger.critical('Data format in file: ' + filename + ', is ' + str(self.file_type) + ' which I cannot understand (right now).')
            self.valid_cnv = False
            return


        # Call the custom header parsing function
        self.parse_custom_header(self.header,self)

        # Trying to extract standard names (p, C, S, T, oxy ... ) from
        # the channel names
        self._get_standard_channel_names(naming_rules)

        self._get_data(raw)
        # Check if we are in the Baltic Sea
        if(baltic == None):
            self.baltic = check_baltic(self.lon,self.lat)
        else:
            self.baltic = baltic
            
        nrec           = numpy.shape(self.raw_data)[0]
        self.units     = {}
        self.names     = {}
        self.names_std = {}
        self.units_std = {}  
        # Check if the dimensions are right
        if(numpy.shape(self.raw_data)[0] > 0):
            if( numpy.shape(self.raw_data)[1] == len(self.channels) ):
                self.data = {}
                # Make a recarray out of the array
                names   = []
                formats = []
                titles  = []
                # Name the columns after the channel names
                for n,c in enumerate(self.channels):
                    names.append(c['name'])
                    formats.append('float')
                    titles.append(c['name_std'])
                    self.data[c['name']]  = self.raw_data[:,n]
                    #if(c['name_std'] not in ('i' + str(c['index']))):
                    #   self.data[c[name_std]]  = self.raw_data[:,n]
                    if(c['name_std'] != None):
                        self.data[c['name_std']]  = self.raw_data[:,n]
                    self.names[c['name']] = c['long_name']
                    self.units[c['name']] = c['unit']
                    self.names_std[c['name_std']] = c['name']
                    self.units_std[c['name_std']] = c['unit']


                # Compute absolute salinity and potential density with the gsw toolbox
                # check if we have enough data to compute
                self.cdata  = None
                self.cunits = {}
                self.cnames = {}
                try:
                    self.data['C0']
                    self.data['T0']
                    self.data['p']
                    FLAG_COMPUTE0 = True # If we have the basic parameter to derive salinity, denisty, N2 ...
                except:
                    FLAG_COMPUTE0 = False

                try:
                    self.data['C1']
                    self.data['T1']
                    self.data['p']
                    FLAG_COMPUTE1 = True
                except:
                    FLAG_COMPUTE1 = False                    

                if FLAG_COMPUTE0:
                    if(not((self.lon == numpy.NaN) or (self.lat == numpy.NaN))):
                        compdata    = self._compute_data(self.data, self.units_std, self.names_std, baltic=baltic,lon=self.lon, lat=self.lat,isen='0')
                    else:
                        compdata    = self._compute_data(self.data, self.units_std, self.names_std, baltic=baltic,isen = '0')


                    self.cdata = compdata[0]
                    self.cunits.update(compdata[1])
                    self.cnames.update(compdata[2])
                else:
                    logger.debug('Not computing data using the gsw toolbox, as we dont have the three standard parameters (C0,T0,p0)')
                # Compute second sensor pair
                if FLAG_COMPUTE1:
                    if(not((self.lon == numpy.NaN) or (self.lat == numpy.NaN))):
                        compdata    = self._compute_data(self.data, self.units_std, self.names_std, baltic=baltic,lon=self.lon, lat=self.lat,isen='1')
                    else:
                        compdata    = self._compute_data(self.data,self.units_std, self.names_std, baltic=baltic,isen = '0')
                    if self.cdata == None:
                        self.cdata = compdata[0]
                    else:
                        self.cdata.update(compdata[0])
                        
                    self.cunits.update(compdata[1])
                    self.cnames.update(compdata[2])
                else:
                    logger.debug('Not computing data using the gsw toolbox, as we dont have the three standard parameters (C1,T1,p)')
                # Add standard names directly to object
                try:                
                    self.p = self.data['p']
                    self.p_unit = self.units_std['p']
                except:
                    pass

                try:                                  
                    self.C = self.data['C0']
                    self.C_unit = self.units_std['C0']
                except:
                    pass

                try:                                    
                    self.T = self.data['T0']
                    self.T_unit = self.units_std['T0']
                except:
                    pass

                try:                                    
                    self.SP = self.cdata['SP00']
                    self.SP_unit = self.cunits['SP00']
                except:
                    pass

                try:                                    
                    self.SA = self.cdata['SA00']
                    self.SA_unit = self.cunits['SA00']
                except:
                    pass

                try:                                    
                    self.CT = self.cdata['CT00']
                    self.CT_unit = self.cunits['CT00']
                except:
                    pass

                try:                                    
                    self.pt = self.cdata['pt00']
                    self.pt_unit = self.cunits['pt00']
                except:
                    pass                                

                try:                                    
                    self.pot_rho = self.cdata['pot_rho00']
                    self.pot_rho_unit = self.cunits['pot_rho00']
                except:
                    pass                                                
                
                # Add pressure for convenience to cdata
                if self.cdata is not None:
                    self.cdata['p'] = self.data['p'][:]
                    self.cunits['p'] = self.units_std['p']
                    self.cnames['p'] = self.names_std['p']
                    # Add oxygen in umol/l to cdata
                    oxyfac    = 1e3  / 22.391
                    oxy_names = ['oxy0','oxy1']
                    for noxy,oxy_name in enumerate(oxy_names):
                        if(oxy_name in self.names_std.keys()):
                            logger.debug('Found ' + oxy_name + ' channel, checking  unit')
                            try:
                                oxyunit = self.units_std[oxy_name].upper()
                            except:
                                oxyunit = None
                            if(oxyunit == 'ML/L'):
                                logger.debug('Found ' + oxy_name + ' channel, unit is ml/l converting to umol/l')
                                self.cdata[oxy_name] = self.data[oxy_name][:]  * oxyfac 
                                self.cunits[oxy_name] = 'umol/l'
                                self.cnames[oxy_name] = self.names_std[oxy_name]
                                if(noxy == 0):
                                    self.oxy = self.cdata[oxy_name]
                                    self.oxy_unit = self.cunits[oxy_name]
                            else:
                                logger.debug('Found ' + str(oxy_name) + ' channel, with unknown unit:' + str(oxyunit))
                                
                
            else:
                logger.warning('Different number of columns in data section as defined in header, this is bad ...')
        else:
            logger.warning('No data in file')
            
            
        self.valid_cnv = True
        
        
    def _compute_data(self,data, units, names, p_ref = 0, baltic = False, lon=0, lat=0, isen = '0'):
        """ Computes convservative temperature, absolute salinity and potential density from input data, expects a recarray with the following entries data['C']: conductivity in mS/cm, data['T']: in Situ temperature in degree Celsius (ITS-90), data['p']: in situ sea pressure in dbar
        
        Arguments:
           p_ref: Reference pressure for potential density
           baltic: if True use the Baltic Sea density equation instead of open ocean
           lon: Longitude of ctd cast default=0
           lat: Latitude of ctd cast default=0
        Returns:
           list [cdata,cunits,cnames] with cdata: recarray with entries 'SP', 'SA', 'pot_rho', etc., cunits: dictionary with units, cnames: dictionary with names 
        """
        sen = isen + isen
        # Check for units and convert them if neccessary
        if(units['C' + isen] == 'S/m'):
            logger.info('Converting conductivity units from S/m to mS/cm')
            Cfac = 10

        if(('68' in units['T' + isen]) or ('68' in names['T' + isen]) ):
            logger.info('Converting IPTS-68 to T90')
            T = gsw.t90_from_t68(data['T' + isen])
        else:
            T = data['T' + isen]
            
        SP = gsw.SP_from_C(data['C' + isen], T, data['p'])
        SA = gsw.SA_from_SP(SP,data['p'],lon = lon, lat = lat)
        if(baltic == True):
            SA = gsw.SA_from_SP_Baltic(SA,lon = lon, lat = lat)
            
        PT = gsw.pt0_from_t(SA, T, data['p'])
        CT = gsw.CT_from_t(SA, T, data['p'])                
        [N2,pN2] = gsw.Nsquared(SA, CT, data['p'])        
        pot_rho                = gsw.pot_rho_t_exact(SA, T, data['p'], p_ref)
        names                  = ['SP' + sen,'SA' + sen,'pot_rho' + sen,'pt0' + sen,'CT' + sen,'N2' + sen,'pN2' + sen]
        formats                = ['float','float','float','float','float']        
        cdata                  = {}
        cdata['SP' + sen]      = SP
        cdata['SA' + sen]      = SA
        cdata['pot_rho' + sen] = pot_rho
        cdata['pt' + sen]      = PT
        cdata['CT' + sen]      = CT
        cdata['N2' + sen]      = N2
        cdata['pN2' + sen]      = pN2        
        cnames           = {'SA' + sen:'Absolute salinity','SP' + sen: 'Practical Salinity on the PSS-78 scale',
                            'pot_rho' + sen: 'Potential density',
                            'pt' + sen:'potential temperature with reference sea pressure (p_ref) = 0 dbar',
                            'CT' + sen:'Conservative Temperature (ITS-90)',
                            'N2' + sen:'Buoyancy frequency',
                            'pN2' + sen:'pressure at the depth of the calculated buoyancy frequency'
                            }
       
        cunits = {'SA' + sen:'g/kg','SP' + sen:'PSU','pot_rho' + sen:'kg/m^3' ,'CT' + sen:'deg C','pt' + sen:'deg C','N2' + sen: '1/s^2','pN2' + sen: 'dbar'}
        
        return [cdata,cunits,cnames]
    
    
    def _get_header(self,raw):
        """ Loops through lines and looks for header. It removes all \r leaving only \n for newline and saves the header in self.header as a string
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

    
    def _parse_header(self):
        """
        Parses the header of the cnv file
        """
        for l in self.header.split('\n'):
            if "* System UpLoad Time" in l:
                line     = l.split(" = ")
                datum = line[1]
                self.upload_date = parse_time(datum)
                #try:
                #    self.upload_date = datetime.datetime.strptime(datum,'%b %d %Y %H:%M:%S')
                #    self.upload_date = self.upload_date.replace(tzinfo=timezone('UTC'))
                #except Exception as e:
                #    logger.warning('_parse_header() upload time: Could not decode time: ( ' + datum + ' ) ' + str(e))

            if("* NMEA Latitude" in l) or ("* NMEA Longitude" in l):
                pos_str = l.rsplit('=')[1]
                pos_str = pos_str.replace("\n","").replace("\r","")
                SIGN = numpy.NaN
                if("S" in pos_str):
                    SIGN = -1.
                    CHAR_NORTH = 'S'
                if("N" in pos_str):
                    SIGN = 1.
                    CHAR_NORTH = 'N'

                if("W" in pos_str):
                    SIGN = -1.
                    CHAR_NORTH = 'W'
                if("E" in pos_str):
                    SIGN = 1.
                    CHAR_NORTH = 'E'
                    
                pos_str = pos_str.replace("  "," ")
                while(pos_str[0] == " "):
                    pos_str = pos_str[1:]                    

                pos_str_deg = pos_str.split(" ")[0]
                pos_str_min = pos_str.split(" ")[1]

                pos = SIGN * float(pos_str_deg) + float(pos_str_min)/60.
                if("* NMEA Latitude" in l):
                    self.lat = pos
                    #print('lat',self.lat)
                if("* NMEA Longitude" in l):
                    self.lon = pos
                    #print('lon',self.lon)
                #print(pos_str,pos_str_deg,pos_str_min,self.lat)
                #input('fds')

            if "* NMEA UTC (Time) = " in l:
                # Like this:
                #* NMEA UTC (Time) = Feb 21 2019 10:18:21
                line     = l.split(" = ")
                line1     = line[1].split(" [")                
                datum = line1[0]
                self.nmea_date = parse_time(datum)
                #try:
                #    self.nmea_date = datetime.datetime.strptime(datum,'%b %d %Y %H:%M:%S')
                #    self.nmea_date = self.nmea_date.replace(tzinfo=timezone('UTC'))
                #except Exception as e:
                #    logger.warning('parse_header() nmea_time: Could not decode time: ( ' + datum + ' )' + str(e))

                    
            if "# start_time = " in l:
                # Like this:
                # start_time = May 03 2018 13:02:01 [Instrument's time stamp, header]
                line     = l.split(" = ")
                line1     = line[1].split(" [")                
                datum = line1[0]
                self.start_date = parse_time(datum)
                #try:
                #    self.start_date = datetime.datetime.strptime(datum,'%b %d %Y %H:%M:%S')
                #    self.start_date = self.start_date.replace(tzinfo=timezone('UTC'))
                #except Exception as e:
                #    logger.warning('parse_header() start_time: Could not decode time: ( ' + datum + ' )' + str(e))                    

            # Look for sensor names and units of type:
            # # name 4 = t090C: Temperature [ITS-90, deg C]
            if "# name" in l:
                lsp = l.split("= ",1)
                sensor = {}
                sensor['index'] = int(lsp[0].split('name')[-1])
                sensor['name'] = lsp[1].split(': ')[0]
                # Test if we have already the name (no double names
                # are allowed later in the recarray struct
                for c,s in enumerate(self.channels):
                    if(s['name'] == sensor['name']):
                        sensor['name'] = sensor['name'] + '@' + str(c)

                # Add a dummy title, this will be later filled with a
                # useful name
                #sensor['name_std'] = 'i' + str(sensor['index'])
                sensor['name_std'] = None
                if(len(lsp[1].split(': ')) > 1): # if we have a long name and unit
                    sensor['long_name'] = lsp[1].split(': ')[1]
                    unit = lsp[1].split(': ')[1]
                    if len(unit.split('[')) > 1 :
                        unit = unit.split('[')[1]
                        unit = unit.split("]")[0]
                        sensor['unit'] = unit
                    else:
                        sensor['unit'] = None
                else:
                    sensor['long_name'] = None
                    sensor['unit'] = None

                self.channels.append(sensor)

            if "# file_type" in l:
                lsp = l.split("= ",1)
                file_type = lsp[1]
                file_type.replace(' ','')
                self.file_type = file_type
        
        
    def _get_standard_channel_names(self, naming_rules):
        """
        Look through a list of rules to try to link names to standard names
        """
        f = open(naming_rules)
        rules = yaml.safe_load(f)
        for r in rules['names']:
            found = False
            #logger.debug('Looking for rule for ' + r['description'])
            logger.debug('Looking for rule for ' + str(r['channels']) + '('+ r['description'] +')')            
            for c in r['channels']:
                if(found == True):
                    found = False
                    break
                for ct in self.channels:
                    if(c in ct['name']):
                        ct['name_std'] = r['name'] # Save the alternative name in the channel
                        logger.debug('Found channel' + str(ct) + ' ' + str(c))
                        found = True
                        break
    
        
        #print('Channels',self.channels)
        
    def _get_data(self,raw):
        """ Reads until the end of the file lines of data and puts them into one big numpy array
        """
        data = []
        nline = 0
        if True:
            for l in raw:
                line_orig = l
                l = l.replace("\n","").replace("\r","")
                l = l.split()
                #data.append (line)
                nline += 1
                try:
                    ldata = numpy.asarray(l,dtype='float')
                    # Get the number of columns with the first line
                    if(nline == 1):
                        ncols = len(ldata)

                    if(len(ldata) == ncols):
                        data.append(ldata)
                except Exception as e:
                    logger.warning('Could not convert data to floats in line:' + str(nline))
                    logger.debug('str:' + line_orig)

            
        self.raw_data = numpy.asarray(data)

        
    def get_info_dict(self):
        """ Returns a dictionary with the essential information
        """
        info_dict = {}
        info_dict['lon']  = self.lon
        info_dict['lat']  = self.lat
        info_dict['date'] = self.date
        try:
            info_dict['station'] = self.iow['station']
        except:
            info_dict['station'] = ''
        info_dict['file'] = self.filename
        info_dict['sha1'] = self.sha1
        info_dict['type'] = 'CNV'        
        return info_dict

    def get_summary(self,header=False):
        """
        Returns a summary of the cnv file in a csv format
        Args:
           header: Returns header only
        """
        
        sep = ','
        rstr = ""
        # Print the header
        if(header):
            rstr += 'date' + sep
            rstr += 'lat' + sep
            rstr += 'lon' + sep
            rstr += 'p min' + sep
            rstr += 'p max' + sep
            rstr += 'num p samples' + sep
            rstr += 'baltic' + sep
            rstr += 'file'  #+ sep
        # Print the file information
        else:
            try:
                rstr += datetime.datetime.strftime(self.date,'%Y-%m-%d %H:%M:%S') + sep
            except: 
                rstr += 'NaN' + sep

            try:
                rstr += '{:8.5f}'.format(self.lat) + sep
                rstr += '{:9.5f}'.format(self.lon) + sep
                

            except:
                rstr += 'NaN' + sep
                rstr += 'NaN' + sep
            pmin = numpy.NaN
            pmax = numpy.NaN
            num_samples = 0                    
            if(self.data != None):
                #print(self.data)
                try:
                    pmin = self.data['p'].min()
                    pmax = self.data['p'].max()
                    num_samples = len(self.data['p'])
                except Exception as e:
                    pass

                                 
            rstr += '{: 8.2f}'.format(pmin) + sep
            rstr += '{: 8.2f}'.format(pmax) + sep
            rstr += '{: 6d}'.format(num_samples) + sep
            rstr += '{: 1d}'.format(int(self.baltic)) + sep            
            rstr += self.filename #+ sep
                
        return rstr

    def get_variables(self):
        """
        Returns a string with all available variables, separated between the originally existing variables within the cnv file (stored in data) and the ones computed and stored in cdata)
        """
        rstr = ''        
        rstr += '#Original variables stored in the file (and in "data"):\n'
        rstr += '#\n'
        rstr += '#\n'        
        rstr += '#Structure:\n'
        rstr += '#Index,name (as in cnv file),standard name (mapped by pycnv), long_name, unit (as in cnv file):\n'

        for n,var in enumerate(self.channels):
            var_name = var['name']
            var_long_name = var['long_name']            
            var_std = var['name_std']
            if(var_std == None):
                var_std = ''            
            unit = var['unit']
            if(unit == None):
                unit = ''
            rstr += str(n) + ';' + var_name + ';' + var_std + ';' + var_long_name + ';' + unit + '\n'


        rstr += '#Computed variables stored in "cdata":\n'
        rstr += '#\n'
        rstr += '#\n'        
        rstr += '#Structure:\n'
        rstr += '#Index,name, long_name, unit (as in cnv file):\n'        
        for n,var in enumerate(self.cdata.keys()):
            rstr += var + ';' + self.cnames[var] + ';' + self.cunits[var] + '\n'

        return rstr
    
    #
    # Plotting functions
    #
    def plot(self,xaxis=['CT00','SA00','oxy0','pot_rho00'],xlims=None,colors=None,
         yaxis='p',ylim=None,show=False,save=False,figsize=[8.27,11.69],fig_prefix
             = './',figure=None):
    #def plot(self,xaxis=['CT00','pot_rho00'],yaxis='p',show=True,save=True):
        """ Plots the data in the cnv file using matplotlib
        Arguments:
           xaxis:
           xlims: The xlimits for the data to plot, if only one list (e.g. [4,5.5]) is given, the range is valid for all data, otherwise a list with the same length as the data to plot is expected (e.g. [[1,2],[3,4],None]), None results in matplotlib automatic xlim
           colors:
           yaxis:
           ylim: The ylimit of the plot, None results in autoscaling
           show:
           save:
           figsize: The size of the figure plotted
           fig_prefix: The prefix put before the figname (this can be a folder together with a file prefix)
           figure: Matplotlib figure for plotting, if None pl.figure() is called

        """
        # Looking for data for y-axis
        try:
            y_data = self.cdata[yaxis]
            y_names = self.cnames[yaxis]
            y_units = self.cunits[yaxis]          
            logger.debug('plot():Found y-axis data (cdata):' + yaxis)
        except Exception as e:
            try:
                y_data = self.data[yaxis]
                y_names = self.names[yaxis]
                y_units = self.units[yaxis]                          
                logger.debug('plot():Found y-axis data (data):' + yaxis)
            except Exception as e:
                logger.warning('plot():Did not find valid y-axis:' + yaxis)
                return

        # Looking for data for x-axis
        x_data       = []
        xaxis_found  = []
        x_names      = []
        x_units      = []
        x_colors     = []
        x_lims     = []        
        for dat_plot in xaxis:
            if dat_plot in self.data:
                #print('Found data to plot in data:' + dat_plot)                
                x_data.append(self.data[dat_plot])
                if dat_plot in self.names:
                    x_names.append(self.names[dat_plot])
                    x_units.append(self.units[dat_plot])
                else:
                    x_names.append(self.names_std[dat_plot])
                    x_units.append(self.units_std[dat_plot])

                xaxis_found.append(dat_plot)
                    
            else:
                if dat_plot in self.cdata:
                    logger.debug('Found data to plot in cdata:' + dat_plot)
                    x_data.append(self.cdata[dat_plot])
                    x_names.append(self.cnames[dat_plot])
                    x_units.append(self.cunits[dat_plot])
                    xaxis_found.append(dat_plot)                    
                    

        # Get the xlims
        if True:
            for n,dat_plot in enumerate(xaxis_found):
                # Check if we have one range or a list of many ranges
                if xlims==None:
                    x_lims.append(None)
                    
                elif(len(xlims) == 2):
                    if (xlims[0] == None) and (xlims[1] == None): # Two Nones
                        x_lims.append(xlims[n])
                        
                    elif type(xlims[0]) != list: # Two numbers
                        x_lims.append(xlims)

                elif(n < len(xlims)):
                    x_lims.append(xlims[n])
                else:
                    x_lims.append(None)


            
        # Get the colors for the data
        x_colors = self._get_colors(xaxis_found,colors)

            
        # Check if we have data to plot
        if len(x_data) == 0:
            logger.warning('plot():Did not find valid x-data:')
            return

        # Check if we got a figure a function argument
        if figure == None:
            fig = pl.figure()
        else:
            fig = figure
        # Set the size to din A4
        fig.set_size_inches(figsize)
        #ax = pl.subplot(1,1,1)
        ax = fig.add_subplot(1,1,1)
        self.figures.append(fig)
        ax_dict = {'figure':fig,'axes':[ax],'x_data':x_data,'x_names':x_names,'x_units':x_units,'y_data':y_data,'y_names':y_names,'y_units':y_units,'x_colors':x_colors,'x_lims':x_lims,'y_lim':ylim}

        # Bookkeeping of all the settings of the plotting axes
        self.axes.append(ax_dict)
        # Drawing the data
        self._draw_data(ax_dict)
        
        if save:
            base_name = os.path.basename(self.filename)
            dstr = self.date.strftime('%Y-%m-%d_%H.%M.%S')        
            fig_name  = dstr + '_' + base_name

            varstr = ''
            for dat_plot in xaxis_found:
                varstr += '_' + dat_plot
                
            #varstr += '_'
            poststr = '.pdf'
            fig_name_final = fig_prefix + fig_name + varstr + poststr
            logger.info('Saving file to file: ' + fig_name_final)
            pl.savefig(fig_name_final)

        if show:
            pl.show()

    def _get_colors(self,names,colors=None):
        """ Function to define a color for the given name
        """
        cmap = pl.cm.Set1
        plot_colors = [None]*len(names)
        # The different data types shall have different colors
        data_types  = {'salt':['SA','SP','sal'],'temp':['CT','T','pt'],'dens':['pot_rho','sigma'],'oxy':['sbeox','oxy']}
        data_colors = {'temp':[(255,0,0),(220,20,60),(178,34,34)],'salt':[(0,0,255),(65,105,225),(0,0,205)],'dens':[(0,0,0),(50,50,50),(128,128,128)],'oxy':[(0,128,0),(34,139,34),(85,107,47)]}
        # Grrr, have to convert it to floats between 0 and 1
        for col in data_colors:
            for c in range(len(data_colors[col])):
                data_colors[col][c] = list(numpy.asarray(data_colors[col][c])/255)
        #cmap = pl.cm.tab20c
        #cmap.N
        num_col = 0
        for n,name in enumerate(names):
            for data_type in data_types:
                if(plot_colors[n] != None):
                    break
                for d in data_types[data_type]:
                    if d in name:
                        #logger.debug('_get_color(): found data type' + data_type)
                        #print('_get_color(): found data type: ' + d)
                        if(len(data_colors[data_type])>0):
                            col = data_colors[data_type].pop()
                        else:
                            num_col +=1
                            col = pl.cm.Set1(num_col)
                            
                        plot_colors[n] = col
                        break

            if(plot_colors == None):
                num_col +=1
                col = pl.cm.Set1(num_col)                
                plot_colors[n] = col
        

        return plot_colors
        
    def _draw_data(self,data):
        """Draws in the axes all the data defined in the given dictionary and
creates additional axes with the same size, if necessary. It will move
the spines of the additional axes such that all ticks are visible

        """

        fig    = data['figure']
        ax     = data['axes'][0]
        xdata  = data['x_data']
        xnames = data['x_names']
        xunits = data['x_units']
        xcolors= data['x_colors']
        xlims= data['x_lims']                
        ydata  = data['y_data']
        ylim   = data['y_lim']
        naxes  = len(xdata)

        # Get the position of the axes
        posx = ax.get_position().get_points()[:,0]
        posy = ax.get_position().get_points()[:,1]
        # Recalculate the axes position in y-direction for the
        # additional data to be plotted
        # Each additional label/ticks needs additional dy
        dy        = 0.1
        dy_fig    = 0.07 # The space needed for the new xlabels
        y_bottom  = []
        y_top     = []
        i_bottom  = -1
        i_top     = -1
        #print('posy',posy)
        for i in range(0,naxes):
            if(i%2 == 0):
                i_bottom += 1
                y_top.append(numpy.NaN)
                y_bottom.append(0 - i_bottom * dy)
            else:
                i_top += 1
                y_bottom.append(numpy.NaN)
                y_top.append(1 + i_top * dy)


        pos_new     = [.05,.05,.9,.9]
        y0_new      = (i_bottom+1) * dy_fig
        top_space   = 0.95 # The remaining space is used for the title
        height_new  = top_space - (i_top+1) * dy_fig - y0_new
        pos_new = [ax.get_position().x0,y0_new,ax.get_position().width,height_new]
        ax.set_position(pos_new)                
        # Create new axes
        for i in range(0,naxes):
            #print('Creating new axes')
            if(i>0):
                # This is a nasty hack, otherwise a same position will result in the same axes
                pos_new[0] += 1e-12
                #data['axes'].append(pl.axes(pos_new))
                data['axes'].append(fig.add_axes(pos_new))
                
            axtmp = data['axes'][-1]
            if(i == 0): # Dont do anything on the original axis
                pass
            else:
                # Taking care of the location of the spines
                axtmp.set_frame_on(True)
                axtmp.patch.set_visible(False)
                axtmp.yaxis.set_ticks(()) # No yticks for all other axes
                for sp in axtmp.spines.values():
                    sp.set_visible(False)

            if(i%2 == 0):
                #print('y_bottom',y_bottom[i])
                axtmp.spines["bottom"].set_position(("axes", y_bottom[i]))
                if(naxes > 1): # Only remove the top spines if we have more than one axes
                    axtmp.spines["top"].set_visible(False)
                axtmp.spines["bottom"].set_color(xcolors[i])                
                axtmp.spines["bottom"].set_visible(True)
                axtmp.xaxis.set_ticks_position("bottom")
                axtmp.xaxis.set_label_position('bottom') 
            else:
                #print('y_top',y_top[i])
                axtmp.spines["top"].set_position(("axes", y_top[i]))
                axtmp.spines["top"].set_visible(True)
                axtmp.spines["top"].set_color(xcolors[i])
                axtmp.spines["bottom"].set_visible(False)                
                axtmp.xaxis.set_ticks_position("top")
                axtmp.xaxis.set_label_position('top') 
                

        # Plotting the data
        # Ylabel
        axtmp = data['axes'][0]
        axtmp.set_ylabel(data['y_names'])
        for i in range(0,naxes):
            axtmp = data['axes'][i]
            if ylim is None:
                axtmp.invert_yaxis()
                ind = range(0,len(ydata))
            else:
                axtmp.set_ylim(ylim)
                ind = (ydata >= min(ylim)) & (ydata <= max(ylim))
                
            pltmp = axtmp.plot(xdata[i][ind],ydata[ind],color=xcolors[i])

            if xlims[i] is not None:
                #print('ranges!')
                axtmp.set_xlim(xlims[i])
            else:
                pass
                #print('no ranges!')
            axtmp.xaxis.label.set_color(xcolors[i])
            axtmp.tick_params(axis='x', colors=xcolors[i])
            #axtmp.xaxis.label.set_label(xnames[i])
            axtmp.set_xlabel(xnames[i] + ' [' + xunits[i] + ']')
        
        # Plotting the title
        
        axtmp = data['axes'][0]
        fs = axtmp.xaxis.get_major_ticks()[0].label.get_fontsize() # Get the fontsize of the ticks
        title_str = ''
        title_str += self.filename + '\n'
        title_str += self.date.strftime('%Y-%m-%d %H:%M:%S') + '; ' 
        title_str += "{:6.3f}".format(self.lat) + 'N; ' + "{:6.3f}".format(self.lon) + 'E'
        axtmp.text(.5,top_space,title_str,ha='center',transform=fig.transFigure,fontsize=fs+2)
        #self._update_plot_style(data)


    def add_sensor(self,sensor, name, data = None, description=None, unit=None):
        """Adds data from an additional sensor to the object, this is
        e.g. used for external sensor attached to the CTD frame but
        eventually merged with the internal CTD data.

        Args:
            sensor:
            name:
            description:
            data:
            unit:

        """
        # Check if we have an external sensor field
        try:
            self.external_sensors
        except Exception as e:
            self.external_sensors = {}

        # Check if we have already the sensorname, if so, leave it but
        # add the sensordata if availabe
        try:
            self.external_sensors[sensor]
        except Exception as e:
            self.external_sensors[sensor] = {'data':{},'names':{},'units':{}}

        if(data is not None):
            self.external_sensors[sensor]['data'][name] = data

        if(description is not None):
            self.external_sensors[sensor]['names'][name] = description
        else:
            self.external_sensors[sensor]['names'][name] = name            

        if(unit is not None):
            self.external_sensors[sensor]['units'][name] = unit
        else:
            self.external_sensors[sensor]['units'][name] = 'unknown'


    def write_nc(self,filename):
        """ Writes a netCDF4 file of the current pycnv object
        """
        print('write_nc() not implemented yet! Sorry for that ...',filename)

        
    def __str__(self):
        """
        String format
        """
        rstr = ""
        rstr += "pycnv of " + self.filename
        rstr += " at Lat: " + str(self.lat)
        rstr += ", Lon: " + str(self.lon)
        rstr += ", Date: " + datetime.datetime.strftime(self.date,'%Y-%m-%d %H:%M:%S')
        return rstr        
            
          
def test_pycnv():
    pycnv("/home/holterma/data/redox_drive/iow_data/fahrten.2011/06EZ1108.DTA/vCTD/DATA/cnv/0001_01.cnv")

# Main function
def main():
    sum_help         = 'Gives a csv compatible summary'
    plot_help        = 'Plots the cnv file, list the parameters in a comma separated list, e.g. --plot CT00,pt00,oxy use the arguments "show" to immidiately show the figure (will halt the code until the figure is closed) and/or "save" to save the figure'
    plot_prefix_help = 'The prefix before the filename, standars is "./", this is usefule to define a path and/or a fie prefix, e.g. --plot_prefix figures/ctd_casts_of_important_cruise__'
    var_help         = 'Lists all the available variables within the file, separated between the orignal data within the file (data) and the computed data (cdata)'        
    sumhead_help     = 'Gives the header to the csv compatible summary'
    parser = argparse.ArgumentParser()
    parser.add_argument('--variables', '-va', action='store_true', help=var_help)    
    parser.add_argument('--summary', '-s', action='store_true', help=sum_help)
    parser.add_argument('--summary_header', '-sh', action='store_true', help=sumhead_help)
    #https://stackoverflow.com/questions/13346540/argparse-optional-argument-before-positional-argument    
    parser.add_argument('--plot', '-p', nargs='?', help=plot_help)
    parser.add_argument('--plot_prefix', '-pre', nargs='?', help=plot_prefix_help)    
    parser.add_argument('--verbose', '-v', action='count')
    #parser.add_argument('--version', action='store_true')
    parser.add_argument('--version', action='version', version='%(prog)s ' + version)
    parser.add_argument('filename')    
    args = parser.parse_args()
    
    if(args.verbose == None):
        loglevel = logging.WARNING        
    elif(args.verbose == 1):
        loglevel = logging.INFO        
    elif(args.verbose == 2):
        loglevel = logging.DEBUG        
    else:
        loglevel = logging.INFO


    logger.setLevel(loglevel)


    filename = args.filename

    print_summary = args.summary
    print_summary_header = args.summary_header
    
    if(filename != None):
        cnv = pycnv(filename,verbosity=loglevel)
    else:
        #logger.critical('Need a filename')
        print(parser.print_help())


    if(args.variables):
        summary = cnv.get_variables()
        print(summary)

    if(print_summary_header):
        summary = cnv.get_summary(header=True)
        print(summary)
    if(print_summary):
        summary = cnv.get_summary()
        print(summary)

    #
    # Plot the file
    #
    if(args.plot != None):
        FLAG_SHOW = False
        FLAG_SAVE = False
        variables_plot = []
        for var in args.plot.split(','):
            if(var.upper() == 'SHOW'):
                FLAG_SHOW = True
            elif( var.upper() == 'SAVE'):
                FLAG_SAVE = True
            else:
                variables_plot.append(var)

        if(args.plot_prefix == None):
            plot_prefix = "./"
        else:
            plot_prefix = args.plot_prefix

        cnv.plot(xaxis=variables_plot,show=FLAG_SHOW,save=FLAG_SAVE,fig_prefix=plot_prefix)

            


#pc = pycnv("/home/holterma/data/redox_drive/iow_data/fahrten.2011/06EZ1108.DTA/vCTD/DATA/cnv/0001_01.cnv")
if __name__ == '__main__':
   main()
    

