import csv
from optparse import OptionParser
import os
import pdb
import progressbar
import sys
import urllib, urllib2
from xml.dom import minidom


# variable init
DEBUG = False
OUTPUT_FILE = "output.csv"
if os.path.exists(OUTPUT_FILE):
    os.remove(OUTPUT_FILE)
output_file = open(OUTPUT_FILE, "a")
#base_url = 'http://gisdata.usgs.gov/XMLWebServices/TNM_Elevation_Service.asmx/getElevation?X_Value=%f&Y_Value=%f&Elevation_Units=meters&Source_Layer=-1&Elevation_Only=1'


# process command line (optparse)
parser = OptionParser()
parser.add_option("-f", "--file", dest="infile", help="input csv file containing WGS84 (lon,lat,site_id) record", metavar="FILE")
(options, args) = parser.parse_args()
if not options.infile:
    print "ERROR: must supply an input file!"
    sys.exit(1)
# open input file
try:
    infile = options.infile
    reader = csv.reader(open(infile, "rb"))
except IOError:
    print "ERROR: Cannot open: " + infile
    sys.exit(1)


# init progress bar
total_lines = sum(1 for line in open(infile))
widgets = ['Downloading: ', progressbar.Percentage(), ' ', progressbar.Bar(marker='=', left='[', right=']'),
           ' ', progressbar.ETA(), ' ', progressbar.FileTransferSpeed()]
progress_bar = progressbar.ProgressBar(widgets=widgets, maxval=total_lines)
progress_bar.start()


# process the csv file
output = ""
for row in reader:
    row_num = int(reader.line_num)
    if row_num == 1:
        continue

    if DEBUG and row_num > 50:
        break

    lon = float(row[1])
    lat = float(row[0])
    site_id = row[2]

    # the base URL of the web service
    url = 'http://gisdata.usgs.gov/XMLWebServices/TNM_Elevation_Service.asmx/getElevation'

    # url GET args
    values = {'X_Value' : lon,
    'Y_Value' : lat,
    'Elevation_Units' : 'meters',
    'Source_Layer' : '-1',
    'Elevation_Only' : '1', }

    # make some fake headers, with a user-agent that will
    # not be rejected by bone-headed servers
    user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    headers = {'User-Agent' : user_agent}

    # encode the GET arguments
    data = urllib.urlencode(values)

    # make the URL into a qualified GET statement:
    get_url = url + '?' + data
        
    flag = 0
    attempt = 1
    while(flag == 0):
        try:
            # make the request: note that by ommitting the url arguments
            # we force a GET request, instead of a POST
            req = urllib2.Request(url=get_url, headers=headers)
            response = urllib2.urlopen(req)
            the_page = response.read()
            flag = 1
        except urllib2.URLError:
            attempt += 1
            print("request fail. trying attempt %s" %(attempt))

        # convert the HTML back into plain XML
        for entity, char in (('lt', '<'), ('gt', '>'), ('amp', '&')):
            the_page = the_page.replace('&%s;' % entity, char)

        # clean some cruft... XML won't parse with this stuff in there...
        the_page = the_page.replace('<string xmlns="http://gisdata.usgs.gov/XMLWebServices/">', '')
        the_page = the_page.replace('<?xml version="1.0" encoding="utf-8"?>\r\n', '')
        the_page = the_page.replace('</string>', '')
        the_page = the_page.replace('<!-- Elevation Values of -1.79769313486231E+308 (Negative Exponential Value) may mean the data source does not have values at that point.  --> <USGS_Elevation_Web_Service_Query>', '')

        # parse the cleaned XML
        dom = minidom.parseString(the_page)
        children = dom.getElementsByTagName('Elevation_Query')[0]

        # extract the interesting parts
        elev = float(children.getElementsByTagName('Elevation')[0].firstChild.data)
        data_source = children.getElementsByTagName('Data_Source')[0].firstChild.data

        # print to stdout

    line = "%f,%f,%f\n" % (lat, lon, elev)
    output_file.write(line)

    progress_bar.update(row_num)

progress_bar.finish()