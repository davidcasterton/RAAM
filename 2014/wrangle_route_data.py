import argparse
import copy
import csv
from math import radians, cos, sin, asin, sqrt
import os
import pdb
import progressbar
import urllib, urllib2
from xml.dom import minidom


DEBUG = False
MIN_WAYPOINT_MILES = 0.25
MAX_WAYPOINT_MILES = 0.5
CLEAN_ROUTE_DIR = os.path.join(os.getcwd(), "timestation_waypoints")
CLEAN_ROUTE_WITH_ELEV_DIR = os.path.join(os.getcwd(), "timestation_waypoints_with_elev")


class GpsWaypoint(object):
    def __init__(self, lat, lon, name=None):
        self.lat = lat
        self.lon = lon
        self.name = name

    def __str__(self):
        return "%f, %f, %s" % (self.lat, self.lon, self.name)

    def get_row(self):
        return [self.lat, self.lon, self.name]


def haversine(waypoint1, waypoint2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    _waypoint1 = copy.deepcopy(waypoint1)
    _waypoint2 = copy.deepcopy(waypoint2)

    if _waypoint1 and _waypoint2:
        # convert decimal degrees to radians
        _waypoint1.lon, _waypoint1.lat, _waypoint2.lon, _waypoint2.lat = map(radians, [_waypoint1.lon, _waypoint1.lat, _waypoint2.lon, _waypoint2.lat])
        # haversine formula
        dlon = _waypoint2.lon - _waypoint1.lon
        dlat = _waypoint2.lat - _waypoint1.lat
        a = sin(dlat/2)**2 + cos(_waypoint1.lat) * cos(_waypoint2.lat) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        #km = 6367 * c
        miles = 3956 * c
    else:
        miles = None

    return miles


def _print(string):
    if DEBUG:
        print(string)


class RaamTrack(object):
    def __init__(self, route_file, timestation_file):
        self.route_file = route_file
        self.timestation_file = timestation_file

        self.timestations = {}

        if not os.path.exists(CLEAN_ROUTE_DIR):
            os.mkdir(CLEAN_ROUTE_DIR)

    class TimeStation(object):
        def __init__(self, waypoint):
            self.waypoint = waypoint
            self.full_name = waypoint.name
            # parse full_name into name & number
            self.number, self.name = self.full_name.split(":")
            self.name = self.name.strip()
            self.number = self.number.strip()
            try:
                self.number = int(self.number.split(" ")[1])
            except IndexError:
                if self.number == "Start":
                    self.number = 0

            # create csv writer
            csv_path = os.path.join(CLEAN_ROUTE_DIR, "%s_%s.csv" % (self.number, self.name))
            if os.path.exists(csv_path):
                os.remove(csv_path)
            fileobj = open(csv_path, "a")
            self.csv_writer = csv.writer(fileobj)
            self.csv_writer.writerow(["Latitude", "Longitude", "Name"])

            self.last_route_waypoint = None

        def extrapolate(self, waypoint1, waypoint2):
            lat = waypoint1.lat + 0.5 * (waypoint2.lat - waypoint1.lat)
            lon = waypoint1.lon + 0.5 * (waypoint2.lon - waypoint1.lon)
            middle_waypoint = GpsWaypoint(lat=lat, lon=lon)

            miles = haversine(waypoint1, middle_waypoint)

            if miles > MAX_WAYPOINT_MILES:
                self.extrapolate(waypoint1, middle_waypoint)
                self.add_route_waypoint(middle_waypoint)
                self.extrapolate(middle_waypoint, waypoint2)
            else:
                self.add_route_waypoint(middle_waypoint)

        def add_route_waypoint(self, waypoint):
            if not self.last_route_waypoint:
                self.csv_writer.writerow(waypoint.get_row())
                self.last_route_waypoint = waypoint
            else:
                miles = haversine(self.last_route_waypoint, waypoint)

                _print("%s (%s), %s miles from previous %s." % (waypoint, self.name, miles, self.last_route_waypoint))

                if miles < MIN_WAYPOINT_MILES:
                    _print("skipping")
                elif miles > MAX_WAYPOINT_MILES:
                    _print("extrapolating")
                    self.extrapolate(self.last_route_waypoint, waypoint)
                else:
                    _print("adding")
                    self.csv_writer.writerow(waypoint.get_row())
                    self.last_route_waypoint = waypoint

    def add_route_waypoint_to_timestation(self, waypoint, timestation_index):
        # check if passed next timestation
        if ((self.timestations.get(timestation_index+1)) and
                (waypoint.lon > self.timestations.get(timestation_index+1).waypoint.lon)):
            print("changing from TS '%s' (longitude %s) to '%s' (longitude %s). current waypoint '%s'" % (
                self.timestations[timestation_index].name, waypoint.lon,
                self.timestations[timestation_index+1].name, self.timestations.get(timestation_index+1).waypoint.lon,
                waypoint))
            timestation_index += 1

        _print("%s adding to %s (%s)" % (waypoint, self.timestations.get(timestation_index).name, timestation_index))

        try:
            timestation = self.timestations.get(timestation_index)
            timestation.add_route_waypoint(waypoint)
        except RuntimeError:
            pdb.set_trace()

        return timestation_index

    def clean_route(self):
        route_reader = csv.reader(self.route_file)
        timestation_reader = csv.reader(self.timestation_file)

        for row in timestation_reader:
            if timestation_reader.line_num == 1:
                continue

            waypoint = GpsWaypoint(lat=float(row[0]), lon=float(row[1]), name=row[2])
            timestation = self.TimeStation(waypoint)
            self.timestations[timestation.number] = timestation

        timestation_index = 0
        for row in route_reader:
            if route_reader.line_num == 1:
                continue

            waypoint = GpsWaypoint(lat=float(row[0]), lon=float(row[1]), name=row[2])

            timestation_index = self.add_route_waypoint_to_timestation(waypoint, timestation_index)

    def add_elevation_to_route(self):
        if not os.path.exists(CLEAN_ROUTE_WITH_ELEV_DIR):
            os.mkdir(CLEAN_ROUTE_WITH_ELEV_DIR)

        for input_file in os.listdir(CLEAN_ROUTE_DIR):
            if input_file.split(".")[1] != "csv":
                continue
            input_path = os.path.join(CLEAN_ROUTE_DIR, input_file)

            reader = csv.reader(open(input_path, "r"))

            output_path = os.path.join(CLEAN_ROUTE_WITH_ELEV_DIR, input_file)
            if os.path.exists(output_path):
                os.remove(output_path)
            writer = csv.writer(open(output_path, "a"))
            writer.writerow(["Latitude", "Longitude", "Name", "Elevation"])

            # init progress bar
            total_lines = sum(1 for line in open(input_path))
            widgets = [input_file, progressbar.Percentage(), ' ', progressbar.Bar(marker='=', left='[', right=']'),
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
                name = row[2]

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

                writer.writerow([lat, lon, name, elev])

                progress_bar.update(row_num)

            progress_bar.finish()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Wrangle RAAM GPS track to have consistent waypoint spacing.')
    parser.add_argument('-route', type=argparse.FileType('r'), dest="route",
                        help='input file, offial RAAM route.')
    parser.add_argument('-timestations', type=argparse.FileType('r'), dest="timestations",
                        help='input file, offial RAAM timestation waypoints.')
    args = parser.parse_args()

    raam_track = RaamTrack(args.route, args.timestations)
    raam_track.clean_route()
    raam_track.add_elevation_to_route()