#
import pycnv
import glob
import fnmatch
import os
import sys
from numpy import *
import argparse
import logging

try:
    from pyproj import Geod
    FLAG_DIST=True
    g = Geod(ellps='WGS84')
except:
    FLAG_DIST=False

# Setup logging module
logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
logger = logging.getLogger('pycnv_sum_folder')

desc = 'A pycnv tool which is recursively searching through the given data_path and searching for cnv files. Found cnv files are parsed and a summary is written to the file given with --filename'
data_help = 'The data path(es) to be searched'
file_help = 'The filename the results are written to'
dist_help = 'Only take files which are within a distance to CTD location'
print_help = 'Prints for each line the summary to stdout'
verb_help = 'Add -v to increase verbosity of command'
parser = argparse.ArgumentParser(description=desc)

parser.add_argument('--data_path', '-d', nargs = '*', required=True,help=data_help)
parser.add_argument('--filename', '-f', default = None,help=file_help)    
parser.add_argument('--distance', '-dist', nargs=3,metavar=('lon [dec deg]','lat [dec deg]','distance [m]'), help=dist_help)
parser.add_argument('--verbose', '-v', action='count',help=verb_help)
parser.add_argument('--print_summary', '-p', action='store_true', help=print_help)

try:
    args = parser.parse_args()
except:
    parser.print_help()
    sys.exit(0)


#args = parser.parse_args()

print_summary = args.print_summary

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
if(filename != None):
    try:
        fi = open(filename,'w')
    except exception as e:
        logger.critical('Could not open file:' + filename)
        logger.critical('Exiting... ')
        exit()

DATA_PATH = args.data_path

logger.info('Will search in folders:' + str(DATA_PATH))


# Distance 
if(args.distance != None):
    londist  = float(args.distance[0])
    latdist  = float(args.distance[1])
    distdist = float(args.distance[2])
    logger.info('Will search for profiles within a ' + str(distdist) + ' m radius around station with longitude ' + str(londist) + ' and latitude ' + str(latdist))
    if(FLAG_DIST == False):
        logger.critical('pyproj is not installed, cannot compute distance, exiting')
        exit()
else:
    FLAG_DIST=False

# Loop through all subfolders
matches = []
for DATA_P in DATA_PATH:
    for root, dirnames, fnames in os.walk(DATA_P):
        #print(root,dirnames,fnames)
        for fname in fnmatch.filter(fnames, '*.cnv'):
            matches.append(os.path.join(root, fname))
            #print(matches[-1])
            if(mod(len(matches),100) == 0):
                logger.info('Found ' + str(len(matches)) + ' files')

        for fname in fnmatch.filter(fnames, '*.CNV'):
            matches.append(os.path.join(root, fname))
            if(mod(len(matches),100) == 0):
                logger.info('Found ' + str(len(matches)) + ' files')
            #print(matches[-1])        


logger.info('Found ' + str(len(matches)) + ' cnv files in folder(s):' + str(DATA_PATH))

save_file = []
files_date = []
if(len(matches) > 0):
    # Write the header of the file
    cnv = pycnv.pycnv(matches[0],verbosity=logging.CRITICAL)    
    if(filename != None):
        summary = cnv.get_summary(header=True)
        fi.write(summary)
        fi.write('\n')

    if(print_summary):
        print(summary)        

    # Loop through all files and make summary
    for i,f in enumerate(matches):
        logger.debug('Parsing file: ' + str(f))
        cnv = pycnv.pycnv(f,verbosity=loglevel)
        files_date.append(cnv.header['date'])
        summary = cnv.get_summary()
        
        FLAG_GOOD = False
        if(FLAG_DIST):
            lon = cnv.header['lon']
            lat = cnv.header['lat']
            if(not(isnan(lon)) and not(isnan(lat))):
                az12,az21,dist = g.inv(lon,lat,londist,latdist)
                if(dist < distdist):
                    FLAG_GOOD = True
        else:
            FLAG_GOOD = True

        if(FLAG_GOOD):
            save_file.append(True)
        else:
            save_file.append(False)

    # Save the with respect to date sorted file
    logger.debug('Writing file')
    ind_sort = argsort(files_date)
    print(files_date)
    print(ind_sort)
    num_wr = 0
    for ind in ind_sort:
        print(ind)
        FLAG_GOOD = save_file[ind]
        if(FLAG_GOOD):
            cnv = pycnv.pycnv(matches[ind],verbosity=logging.CRITICAL)    
            summary = cnv.get_summary()
            if(filename != None):
                fi.write(summary)
                fi.write('\n')
                fi.flush()
                num_wr +=1


else:
    print('No files found ... ')

if(filename != None):
    logger.info('Wrote ' +str(num_wr) + ' datasets into file:' + filename)
    fi.close()


    
