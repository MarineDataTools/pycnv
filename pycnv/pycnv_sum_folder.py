#
#import pycnv
from . import pycnv as pycnv
import glob
import fnmatch
import os
import sys
import numpy
import argparse
import logging
import pkg_resources
import yaml
from pytz import timezone
import datetime


# Get the version
version_file = pkg_resources.resource_filename('pycnv','VERSION')

with open(version_file) as version_f:
   version = version_f.read().strip()

try:
    from pyproj import Geod
    FLAG_PYPROJ=True
    g = Geod(ellps='WGS84')
except:
    FLAG_PYPROJ=False

# Setup logging module
logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
logger = logging.getLogger('pycnv_sum_folder')


def get_stations():
    stations_file = pkg_resources.resource_filename('pycnv', 'stations/iow_stations.yaml')
    f_stations = open(stations_file)
    # use safe_load instead load
    stations_yaml = yaml.safe_load(f_stations)
    return stations_yaml['stations']
    
def get_all_valid_files(DATA_FOLDER, loglevel = logging.INFO, station = None, save_summary = False, status_function = None, start_time = None, stop_time = None):
    """
    Args:
       DATA_FOLDER: Either list of data_folder or string of one data_folder
       station: CTD cast has to lie within radius around position, given as a list with longitude [decdeg], latitude [decdeg], radius [m], e.g. [20.0,54.0,5000], if station has 4 arguments it is treated as a rectangle with [lon0,lat0,lon1,lat1] and the cast has to be within lon0 and lon1 as well as lat0 and lat1
       status_function: A function that is called during reading, the function is called with the current filenumber i, the total number of files nf and the filename f, e.g. function(i,nf,f) 
       start_time: Casts date need to be after start time [datetime]
       stop_time: Casts date need to be before stop time [datetime]
    Returns:
        Dictionary with data
    """

    if(isinstance(DATA_FOLDER, str)):
        DATA_FOLDER = [DATA_FOLDER]
    if station == None:
        FLAG_DIST = False
    else:
        if(len(station) == 3): # Sphere with radius
            londist   = station[0]
            latdist   = station[1]
            distdist  = station[2]
            FLAG_DIST = True            
        elif(len(station) == 4): # Rectangle
            londist   = station[0]
            latdist   = station[1]
            londist2   = station[2]
            latdist2   = station[3]            
            distdist  = -9999
            FLAG_DIST = True
        else:
            logger.info('Defined position threshold with wrong parameters')
            FLAG_DIST = False            


    if (type(start_time) == datetime.datetime) or (type(stop_time) == datetime.datetime):
        FLAG_TIME = True
        # Check if one of the two is not a datetime
        if(type(start_time) is not datetime.datetime):
            start_time = datetime.datetime(1,1,1, tzinfo=timezone('UTC'))
        if(type(stop_time) is not datetime.datetime):
            stop_time = datetime.datetime(3000,1,1, tzinfo=timezone('UTC'))            
    else:
        FLAG_TIME = False        
        
    #
    # Loop through all subfolders
    #
    matches = []
    for DATA_P in DATA_FOLDER:
        for root, dirnames, fnames in os.walk(DATA_P):
            #print(root,dirnames,fnames)
            for fname in fnmatch.filter(fnames, '*.cnv'):
                matches.append(os.path.join(root, fname))
                #print(matches[-1])
                if(numpy.mod(len(matches),100) == 0):
                    logger.info('Found ' + str(len(matches)) + ' files')

            for fname in fnmatch.filter(fnames, '*.CNV'):
                matches.append(os.path.join(root, fname))
                if(numpy.mod(len(matches),100) == 0):
                    logger.info('Found ' + str(len(matches)) + ' files')
                #print(matches[-1])        


    logger.info('Found ' + str(len(matches)) + ' cnv files in folder(s):' + str(DATA_FOLDER))
    if(len(matches) == 0):
        if(status_function is not None):
            print('Status function nothing found')
            status_function(0,0,'Nothing found')        
        return {'files':[],'dates':[],'lon':[],'lat':[],'info_dict':[]}
    save_file       = []
    files_date      = []
    file_names_save = []
    files_lon_save  = []
    files_lat_save  = []        
    files_date_save = []
    files_summary   = []
    files_info_dict = []    
    if(len(matches) > 0):
        # Write the header of the file
        #print('Hallo',matches[0])
        cnv = pycnv(matches[0],verbosity=logging.CRITICAL)

        # Loop through all files and make summary
        nf = len(matches)
        for i,f in enumerate(matches):
            logger.info('Parsing file ' + str(i) +'/' + str(nf) + ': ' + str(f))
            if(status_function is not None):
                #print('Status function')
                status_function(i,nf,f)
            cnv = pycnv(f,verbosity=loglevel)
            if(cnv.valid_cnv):
                files_date.append(cnv.date)
                summary = cnv.get_summary()
                FLAG_GOOD_DIST = False
                FLAG_GOOD_TIME = False
                # Check if we are within a distance
                lon = cnv.lon
                lat = cnv.lat
                if(FLAG_TIME):
                    if((cnv.date > start_time) and (cnv.date < stop_time)):
                        FLAG_GOOD_TIME = True
                else:
                    FLAG_GOOD_TIME = True
                    
                if(FLAG_DIST):
                    if(not(numpy.isnan(lon)) and not(numpy.isnan(lat))):
                        print('Distance')
                        if(distdist > 0): # Radius defined
                            az12,az21,dist = g.inv(lon,lat,londist,latdist)
                            print('Radius, distance:' + str(dist) + ' m')
                            if(dist < distdist):
                                print('Radius good')
                                FLAG_GOOD_DIST = True
                            else:
                                print('Too far away')
                        else: # Rectangle defined
                            print('Rectangle')
                            if((lon >= londist) and (lon <= londist2) and (lat >= latdist) and (lat <= latdist2)):
                                print('Rectangle good')
                                FLAG_GOOD_DIST = True

                else:
                    FLAG_GOOD_DIST = True

                if(FLAG_GOOD_DIST and FLAG_GOOD_TIME):
                    save_file.append(True)
                    file_names_save.append(f)
                    files_date_save.append(cnv.date)
                    files_lon_save.append(lon)
                    files_lat_save.append(lat)
                    files_summary.append(summary)
                    files_info_dict.append(cnv.get_info_dict()) # This will be the standard for future development
                else:
                    save_file.append(False)

        # Save the with respect to date sorted file
        logger.info('Sorting all files')
        # Replace invalid dates with an obviously wrong date to be able to sort them
        for i in range(len(files_date_save)):
            if(files_date_save[i] == None):
                files_date_save[i] = datetime.datetime(1,1,1).replace(tzinfo=timezone('UTC'))

        ind_sort = numpy.argsort(files_date_save)                
        file_names_save_sort = list(numpy.asarray(file_names_save)[ind_sort])
        retdata  = {'files':file_names_save_sort,'dates':list(numpy.asarray(files_date_save)[ind_sort]),'lon':list(numpy.asarray(files_lon_save)[ind_sort]),'lat':list(numpy.asarray(files_lat_save)[ind_sort]),'info_dict':list(numpy.asarray(files_info_dict)[ind_sort])}

        if save_summary:
            summary_array = numpy.asarray(files_summary)[ind_sort]
            retdata['summary'] = summary_array
        
        return retdata


def main():

    example1 = 'Example (searching in folders fahrten.2011 and fahrten.2012 for stations TF0286 within a radius of 5000m: pycnv_sum_folder -d fahrten.201[12]/ -f tf286.txt --station TF0286 5000'

    desc             = 'A pycnv tool which is recursively searching through the given data folder and searching for cnv files. Found cnv files are parsed and a summary is written to the file given by --filename. '
    desc += example1

    data_help        = 'The data path(es) to be searched'
    file_help        = 'The filename the results are written to'
    dist_help        = 'Only take files which are within a distance to CTD location'
    station_help     = 'Only take files which are within a distance to station'
    stationlist_help = 'Lists all known stations with their names and positions'
    print_help       = 'Prints for each line the summary to stdout'
    verb_help        = 'Add -v to increase verbosity of command'
    parser           = argparse.ArgumentParser(description=desc)


    parser.add_argument('--data_folder', '-d'  , nargs = '*', required=False, help=data_help)
    parser.add_argument('--filename', '-f'   , default = None,help=file_help)
    parser.add_argument('--distance', '-dist', nargs=3,metavar=('lon [dec deg]','lat [dec deg]','distance [m]'), help=dist_help)
    parser.add_argument('--station', '-s'    , nargs=2,metavar=('Station name','distance [m]'), help=station_help)
    parser.add_argument('--list_stations'    , '-ls', action='store_true', help=stationlist_help)
    parser.add_argument('--verbose', '-v'    , action='count',help=verb_help)
    parser.add_argument('--print_summary'    , '-p', action='store_true', help=print_help)
    parser.add_argument('--version', action='version', version='%(prog)s ' + str(version))

    args = parser.parse_args()

    #args = parser.parse_args()
    # Constraints for the cnv files to search
    constraint_station = None
    print_summary = args.print_summary

    if(args.verbose == None):
        loglevel = logging.INFO
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
    if(filename != None):
        try:
            fi = open(filename,'w')
        except exception as e:
            logger.critical('Could not open file:' + filename)
            logger.critical('Exiting... ')
            exit()



    #
    # Distance option, and no station is defined
    #
    if(args.distance != None and args.station == None):
        FLAG_DIST=True
        londist  = float(args.distance[0])
        latdist  = float(args.distance[1])
        distdist = float(args.distance[2])
        # Creating a dictionary for the get_valid_files function
        constraint_station = [None,None,None] 
        constraint_station[0]  = londist
        constraint_station[1]  = latdist
        constraint_station[2]  = distdist                            
        logger.info('Will search for profiles within a ' + str(distdist) + ' m radius around station with longitude ' + str(londist) + ' and latitude ' + str(latdist))
        if(FLAG_PYPROJ == False):
            logger.critical('pyproj is not installed, cannot compute distance, exiting')
            exit()
    else:
        FLAG_DIST=False



    #
    # Read stations file
    #
    #print(args.list_stations,args.station)
    if(args.list_stations or args.station != None):
        FLAG_DIST=False
        if(args.station != None):
            logger.info('Looking for station with name:' + args.station[0])
            sname_tmp = args.station[0]
        else:
            sname_tmp = None
        stations_file = pkg_resources.resource_filename('pycnv', 'stations/iow_stations.yaml')
        print('Stations file:',stations_file)
        f_stations = open(stations_file)
        # use safe_load instead load
        stations_yaml = yaml.safe_load(f_stations)
        f_stations.close()

        for i,station in enumerate(stations_yaml['stations']):
            namestation = [station['name']]
            lonstation  = station['longitude']
            latstation  = station['latitude']
            try:
                anames = station['alternative_names']
            except:
                anames = []

                
            namestation.extend(anames)
            for sname in namestation:
                if(sname == sname_tmp):
                    FLAG_DIST=True
                    logger.info('Found station')
                    londist  = lonstation
                    latdist  = latstation
                    distdist = float(args.station[1])
                    # Creating a dictionary for the get_valid_files function
                    constraint_station = [None,None,None]
                    constraint_station[0]  = londist
                    constraint_station[1]  = latdist
                    constraint_station[2]  = distdist                    
                    logger.info('Will search for profiles within a ' + str(distdist) +\
                                 ' m radius around station ' + str(sname) + ' with longitude '\
                                  + str(londist) + ' and latitude ' + str(latdist))
                    if(FLAG_PYPROJ == False):
                        logger.critical('pyproj is not installed, cannot compute distance, exiting')
                        sys.exit(1)


            if(args.list_stations == True):
                print(namestation,lonstation,latstation)

        if(FLAG_DIST == False and sname_tmp != None):
            logger.critical('Could not find a station with name ' + args.station[0] +  ' in station file, exiting.')
            sys.exit(1)


    if(args.list_stations == True):
        sys.exit(0)


    if(args.data_folder != None):
        DATA_FOLDER = args.data_folder
        logger.info('Will search in folders:' + str(DATA_FOLDER))
    else:
        parser.print_help()
        logger.critical('Specify a data path to search for cnv files ... exiting')
        sys.exit(0)

    # Read in all potential cnv files, this "double" reading is (probably)
    # necessary for sorting them without saving all the data into RAM
    # TODO, if more speed is needed more data can be saved into cnv_data
    logger.info('Checking for double datasets')
    cnv_data = get_all_valid_files(DATA_FOLDER, loglevel = loglevel, station = constraint_station, save_summary = True)
    # Searching for files with the same origin (but probably different postprocessing of the seabird software)
    lon_d      = numpy.asarray(cnv_data['lon'])
    lat_d      = numpy.asarray(cnv_data['lat'])
    date_d     = numpy.asarray(cnv_data['dates'])
    checked_d  = numpy.zeros(len(lon_d),dtype=int)
    num_d      = numpy.zeros(len(lon_d),dtype=int)

                    
    for i in range(len(lon_d)):
        if(checked_d[i] == 0):
            checked_d[i]       = 1
            ind_date           = date_d[i] == date_d
            ind_lon            = lon_d[i] == lon_d
            ind_lat            = lat_d[i] == lat_d
            ind_all            = ind_date & ind_lon & ind_lat
            checked_d[ind_all] = 1
            num_d[ind_all]     = num_d.max() + 1

    
    file_names_save = cnv_data['files']
    # Save the valid files into the specified file or print it to console
    if True:
        num_wr = 0
        for nf,fname in enumerate(file_names_save):
            #FLAG_GOOD = save_file[ind]
            #if(FLAG_GOOD):
                #cnv = pycnv.pycnv(matches[ind],verbosity=logging.CRITICAL)
            if True:
                if(nf == 0):
                    cnv        = pycnv(fname,verbosity=logging.CRITICAL)
                    cnv_header = cnv.get_summary(header=True)                
                    #summary    = cnv.get_summary()
                    
                summary = cnv_data['summary'][nf]
                    
                # Adding information about double files
                sep = ','
                summary = '{:5d}'.format(nf) + sep + '{:5d}'.format(num_d[nf]) + sep + summary
                cnv_header = 'num file'+ sep + 'num double' + sep + cnv_header
                if(print_summary):
                    if(nf == 0):
                        print(cnv_header)
                        
                    print(summary)
                if(filename != None):
                    if(nf == 0):
                        fi.write(cnv_header)
                        fi.write('\n')
                    fi.write(summary)
                    fi.write('\n')
                    fi.flush()
                    num_wr +=1

    else:
        print('No files found ... ')

    nunique = 0
    if(len(num_d) > 0):
        nunique = num_d.max()
    logger.info('Read ' +str(len(file_names_save)) + ' files (' + str(nunique) + ' with unique datasets)')
    if(filename != None):
        logger.info('Wrote ' +str(num_wr) + ' datasets into file:' + filename)
        fi.close()



if __name__ == '__main__':
   main()    


    
