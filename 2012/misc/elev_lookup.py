# nice CLI interface
import sys
from optparse import OptionParser

# url access
import urllib, urllib2

# simple XML parsing
from xml.dom import minidom

# CSV file parsing
import csv


# define service URL
base_url = 'http://gisdata.usgs.gov/XMLWebServices/TNM_Elevation_Service.asmx/getElevation?X_Value=%f&Y_Value=%f&Elevation_Units=meters&Source_Layer=-1&Elevation_Only=1'


#process command line (optparse)
parser = OptionParser()
parser.add_option("-f", "--file", dest="infile", help="input csv file containing WGS84 (lon,lat,site_id) record", metavar="FILE")


# process args
(options, args) = parser.parse_args()

#require an input file
if not options.infile:
        print "ERROR: must supply an input file!"
        sys.exit(1)


#open input file
try:
        infile = options.infile
        reader = csv.reader(open(infile, "rb"))
except:
        print "ERROR: Cannot open: " + infile
        sys.exit(1)


# read the csv file
output = ""
row_num = 0
for row in reader:
	if row_num == 0:
		row_num += 1
		continue

	#row_num += 1
	#if row_num > 50:
	#	break

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
	while(flag==0):
		try:
		        # make the request: note that by ommitting the url arguments
        		# we force a GET request, instead of a POST
		        req = urllib2.Request(url=get_url, headers=headers)
        		response = urllib2.urlopen(req)
	        	the_page = response.read()
			flag = 1
		except:
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
	output += "%f,%f,%f\n" % (lat, lon, elev)
        print "%f,%f,%s,%f,%s" % (lon, lat, site_id, elev, data_source)

f = open("output.csv","w")
f.write(output)
