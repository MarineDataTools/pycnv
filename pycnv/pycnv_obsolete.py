import datetime
from pytz import timezone
from numpy import *
import logging
import sys
import argparse

    

# TODO: add NMEA position, time

# Setup logging module
logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
logger = logging.getLogger('pycnv')


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


def extract_cnv_data(filename,only_metadata = False):
    """
    
    @author: Robert Mars, IOW
    modified and improved by Peter Holtermann, IOW

    Args:
        filename: filename of the cnv file
        only_metadata: True/False, if true no data is read in and only the header with the metadata is returned
    
    """    

    kanal_namen = []
    units = []
    data = []
    ######
    header_end = False
    fh_in = open(filename, "r")
    # Loop through lines and parse header/data
    for nl,line in enumerate(fh_in):
        ###### Datum und Uhrzeit der Station ermitteln 
        if "System UpLoad Time" in line:
            line = line.split(" ")
            monat = line[5]
            tag = line[6]
            jahr = line[7]
            datum_up = date_correction(tag, monat, jahr)
            zeit_up = line[8].replace("\n","").replace("\r","")
#            print("%s" % datum)
#            print("%s" % zeit)
        # if "System UpLoad Time" is not in header
        elif "start_time" in line:
            #print(line)
            try:
                line = line.split(" ")
                monat = line[3]
                tag = line[4]
                jahr = line[5]
                datum = date_correction(tag, monat, jahr)
                zeit = line[6].replace("\n","").replace("\r","")
            except Exception as e:
                logger.warning('start_time parsing error:' + str(e))
                logger.warning('start_time str:' + line_orig)                
                
#            print("%s" % datum)
#            print("%s" % zeit)
        elif  "Startzeit" in line:
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
            except Exception as e:
                logger.warning('Startzeit parsing error:' + str(e))
                logger.warning('Startzeit str:' + line_orig)
            
        ###### Meta-Daten der Reise und Station
        elif "ReiseNr" in line:
            line = line.split("=")
            reise = line[1]
            reise = reise.replace(" ","")
            reise = reise.replace("\n","").replace("\r","")
            # print("Reise: %s" % reise)
        elif "StatBez" in line:
            line = line.split("=")
            station_bez = line[1]
            # station_bez = station_bez.replace(" ","")
            station_bez = station_bez.replace("\n","").replace("\r","")
            # print("Station: %s" % station_bez)
        elif "EinsatzNr" in line:
            line = line.split("=")
            einsatz_nr = line[1]
            einsatz_nr = einsatz_nr.replace(" ","")
            einsatz_nr = einsatz_nr.replace("\n","").replace("\r","")
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
                
        # Get indices of data columns
        elif "# name" in line:
            line = line.split("= ")
            # line[1] = line[1].replace("\n","")
            line[1] = line[1].replace("\n","").replace("\r","")
            kanal_namen.append(line[1])
            # print(line[1])
            line = line[1].split("[")
            # print(line)
            if len(line) > 1 :
                line = line[1].split("]")
                # print(line)
                units.append (line[0])
            else: 
                # print("no unit")
                units.append ("no unit defined")
        elif "*END*" in line:
            # print(kanal_namen)
            ### Ende des Headers markieren --> Beginn der Daten
            header_end = True
            continue
        #
        # Read the data
        #
        if(header_end == True and only_metadata == False):
            line_orig = line
            line = line.replace("\n","").replace("\r","")
            line = line.split()
            #data.append (line)
            try:
                parsed_data = asarray(line,dtype='float')
                # Check if we read the same amount of channels
                if(len(parsed_data) == len(kanal_namen)):
                    data.append(parsed_data)
            except Exception as e:
                logger.warning('Could not convert data to floats in line:' + str(nl))
                logger.debug('str:' + line_orig)

            
    data = asarray(data)
    
    if 'reise' not in locals():
        reise = "unknown"
    if 'station_bez' not in locals():
        station_bez = "unknown"
    if 'einsatz_nr' not in locals():
        einsatz_nr = "unknown"
    if 'serie_nr' not in locals():
        serie_nr = "unknown"
    if 'operator' not in locals():
        operator = "unknown"
    if 'latitude' not in locals():
        latitude = "unknown"
        lat = NaN
    if 'longitude' not in locals():
        longitude = "unknown"
        lon = NaN

    # Check which date/time information to use
    if 'datum' not in locals():
        if('datum_up' in locals()):
            datum = datum_up
            zeit = zeit_up
        if('datum_start' in locals()):
            datum = datum_start
            zeit = zeit_start
        else:
            datum = None
            zeit = None            

    #print(datum,zeit)
    # Create the header
    header = [datum, reise,station_bez,einsatz_nr,serie_nr,operator,latitude,longitude,zeit]
    header_dict = {}
    #if(datum != None):
    try:
        header_dict['date'] = datetime.datetime.strptime(datum + zeit,'%Y-%m-%d%H:%M:%S')
        header_dict['date'].replace(tzinfo=timezone('UTC'))
    except:
    #else:
        header_dict['date'] = None
        
    header_dict['mission'] = reise
    header_dict['mission_nr'] = einsatz_nr
    header_dict['operator'] = operator
    header_dict['station'] = station_bez
    header_dict['lat'] = lat
    header_dict['lon'] = lon
    header_dict['latstr'] = latitude
    header_dict['lonstr'] = longitude
    # Append header and data
    data_return = {}
    data_return['header'] = header_dict
    data_return['channel_names'] = kanal_namen
    data_return['data'] = data
    data_return['units'] = units
    #return(header,header_dict,kanal_namen,data,units)
    return data_return


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
    def __init__(self,filename, only_metadata = False,verbosity = logging.INFO):
        """
        """
        logger.setLevel(verbosity)
        logger.info(' Opening file: ' + filename)
        # Parsing the data
        raw_data = extract_cnv_data(filename, only_metadata = False)
        self.filename = filename
        self.raw_data = raw_data
        self.header = raw_data['header']
        self.data = None
        self.derived = {}
        if(only_metadata):
            return
        # Fill the object with the data
        else:
            self.data_str = raw_data['data']
            if(len(self.data_str) > 0):
                self.data = {}
                self.units = {}
                data_ar = asarray(raw_data['data'])
                for ind,channel_name in enumerate(raw_data['channel_names']):
                    if('prDM:' in channel_name):
                        logger.debug('Found pressure sensor (Digiquartz)')
                        self.data['p'] = data_ar[:,ind]
                        self.units['p'] = channel_name
                        
                    elif('pr:' in channel_name):
                        logger.debug('Found pressure sensor')
                        self.data['p'] = data_ar[:,ind]
                        self.units['p'] = channel_name
                        
                    if('depS:' in channel_name):
                        logger.debug('found depth in salt water channel')
                        self.data['depS'] = data_ar[:,ind]
                        self.units['depS'] = channel_name
                        
                    if('t090C:' in channel_name) or ('t090:' in channel_name):
                        logger.debug('Found first temperature sensor')
                        self.data['temp0'] = data_ar[:,ind]
                        self.units['temp0'] = channel_name

                    if('t190C:' in channel_name) or ('t190:' in channel_name):
                        logger.debug('Found second temperature sensor')
                        self.data['temp1'] = data_ar[:,ind]
                        self.units['temp1'] = channel_name

                    if('c0mS/cm:' in channel_name):
                        logger.debug('Found first conductivity sensor')
                        self.data['cond0'] = data_ar[:,ind]
                        self.units['cond0'] = channel_name

                    if('c1mS/cm:' in channel_name):
                        logger.debug('Found second conductivity sensor')
                        self.data['cond1'] = data_ar[:,ind]
                        self.units['cond1'] = channel_name

                    #if('sal00:' in channel_name):
                    #    logger.debug('Found salinity record')
                    #    self.data['sal11'] = data_ar[:,ind]
                    #    self.units['sal11'] = channel_name

                    if('sal00:' in channel_name):
                        logger.debug('Found salinity 0 record')
                        self.data['sal00'] = data_ar[:,ind]
                        self.units['sal00'] = channel_name

                    if('sal11:' in channel_name):
                        logger.debug('Found salinity 1 record')
                        self.data['sal11'] = data_ar[:,ind]
                        self.units['sal11'] = channel_name

                    if('sbeox0' in channel_name):
                        logger.debug('Found oxygen 0 record')
                        self.data['oxy0'] = data_ar[:,ind]
                        self.units['oxy0'] = channel_name

                    if('sbeox1' in channel_name):
                        logger.debug('Found oxygen 1 record')
                        self.data['oxy1'] = data_ar[:,ind]
                        self.units['oxy1'] = channel_name                                                
            else:
                print('No data in the file')
                return
                

    def derive(self,property):
        """

        Derives seawater properties as salinity, buoyancy frequency squared etc.
        Args:
            ST:
            N2:
        """

        try:
            gsw
        except:
            logger.warning('GSW toolbox missing, derive will not work, doing nothing')
            return
        
        if(property == 'ST'):
            # Poor mans check if the variables exist
            sensor_pair0 = False
            sensor_pair1 = False
            try:
                tmp1 = self.data['cond0']
                tmp1 = self.data['temp0']
                tmp1 = self.data['p']
                sensor_pair0 = True
            except:
                sensor_pair0 = False

            try:
                tmp1 = self.data['cond1']
                tmp1 = self.data['temp1']
                tmp1 = self.data['p']
                sensor_pair1 = True
            except:
                sensor_pair1 = False                
                
                
            if(sensor_pair0):
                logger.debug('Calculating PSU0/SA11/CT11/rho11')
                SP = gsw.SP_from_C(self.data['cond0'],self.data['temp0'],self.data['p'])
                self.derived['SP00'] = SP
                SA = gsw.SA_from_SP(SP,self.data['p'],self.header['lon'],self.header['lat'])
                self.derived['SA00'] = SA
                CT = gsw.CT_from_t(SA,self.data['temp0'],self.data['p'])
                self.derived['CT00'] = CT
                rho = gsw.rho_CT_exact(SA,CT,self.data['p'])
                self.derived['rho00'] = rho
            if(sensor_pair1):
                logger.debug('Calculating PSU1/SA11/CT11/rho11') 
                SP = gsw.SP_from_C(self.data['cond1'],self.data['temp1'],self.data['p'])
                self.derived['SP11'] = SP
                SA = gsw.SA_from_SP(SP,self.data['p'],self.header['lon'],self.header['lat'])
                self.derived['SA11'] = SA
                CT = gsw.CT_from_t(SA,self.data['temp1'],self.data['p'])
                self.derived['CT11'] = CT
                rho = gsw.rho_CT_exact(SA,CT,self.data['p'])
                self.derived['rho11'] = rho                
                
                
        if(property == 'N2'):
            # Poor mans check if the variables exist
            sensor_pair0 = False
            sensor_pair1 = False
            try:
                tmp1 = self.derived['SA00']
                tmp1 = self.derived['CT00']                
                tmp1 = self.data['p']
                sensor_pair0 = True
            except:
                logger.info('Did not find absolute salinities and temperature, do first a .derive("ST")')
                sensor_pair0 = False

            try:
                tmp1 = self.derived['SA11']
                tmp1 = self.derived['CT11']                
                tmp1 = self.data['p']
                sensor_pair1 = True
            except:
                logger.info('Did not find absolute salinities and temperature, do first a .derive("ST")')
                sensor_pair1 = False

            if(sensor_pair0):
                logger.debug('Calculating Nsquared00')
                [N2,p_mid] = gsw.Nsquared(self.derived['SA00'],self.derived['CT00'],self.data['p'])
                self.derived['Nsquared00'] = interp(self.data['p'],p_mid,N2)
            if(sensor_pair1):
                logger.debug('Calculating Nsquared11')                
                [N2,p_mid] = gsw.Nsquared(self.derived['SA11'],self.derived['CT11'],self.data['p'])
                self.derived['Nsquared11'] = interp(self.data['p'],p_mid,N2)
                
                
        if(property == 'alphabeta'):
            # Poor mans check if the variables exist
            sensor_pair0 = False
            sensor_pair1 = False
            try:
                tmp1 = self.derived['SA00']
                tmp1 = self.derived['CT00']                
                tmp1 = self.data['p']
                sensor_pair0 = True
            except:
                logger.info('Did not find absolute salinities and temperature, do first a .derive("ST")')
                sensor_pair0 = False

            try:
                tmp1 = self.derived['SA11']
                tmp1 = self.derived['CT11']                
                tmp1 = self.data['p']
                sensor_pair1 = True
            except:
                logger.info('Did not find absolute salinities and temperature, do first a .derive("ST")')
                sensor_pair1 = False
                

            if(sensor_pair0):
                logger.debug('Calculating Nsquared00')
                alpha = gsw.alpha(self.derived['SA00'],self.derived['CT00'],self.data['p'])
                beta = gsw.beta(self.derived['SA00'],self.derived['CT00'],self.data['p'])
                self.derived['alpha00'] = alpha
                self.derived['beta00'] = beta
            if(sensor_pair1):
                logger.debug('Calculating Nsquared11')                
                alpha = gsw.alpha(self.derived['SA11'],self.derived['CT11'],self.data['p'])
                beta = gsw.beta(self.derived['SA11'],self.derived['CT11'],self.data['p'])
                self.derived['alpha11'] = alpha
                self.derived['beta11'] = beta

    def get_summary(self,header=False):
        """
        Returns a summary of the cnv file in a csv format
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
                rstr += datetime.datetime.strftime(self.header['date'],'%Y-%m-%d %H:%M:%S') + sep
            except: 
                rstr += 'NaN' + sep
            rstr += str(self.header['lat']) + sep
            rstr += str(self.header['lon']) + sep
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


if __name__ == '__main__':
    main()
    

