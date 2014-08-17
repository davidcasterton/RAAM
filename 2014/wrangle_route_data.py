import argparse
import copy
import csv
from math import radians, cos, sin, asin, sqrt
import os
import pdb
import progressbar
import urllib, urllib2
from xml.dom import minidom

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as colors

OUTPUT_DIR = os.path.join(os.getcwd(), "output")
DEBUG = False
MIN_WAYPOINT_MILES = 0.45
MAX_WAYPOINT_MILES = 0.55


class GpsWaypoint(object):
    def __init__(self, lat, lon, name=None):
        self.lat = lat
        self.lon = lon
        self.name = name
        self.elevation = None

    def __str__(self):
        string = "%f, %f, %s" % (self.lat, self.lon, self.name)
        if self.elevation:
            string += ", %s" % (self.elevation)
        return string

    def get_row(self):
        return [self.lat, self.lon, self.name]

    def add_elevation(self):
        # the base URL of the web service
        url = 'http://gisdata.usgs.gov/XMLWebServices/TNM_Elevation_Service.asmx/getElevation'

        # url GET args
        values = {'X_Value' : self.lon,
        'Y_Value' : self.lat,
        'Elevation_Units' : 'meters',
        'Source_Layer' : '-1',
        'Elevation_Only' : '1', }

        # make some fake headers, with a user-agent that will
        # not be rejected by bone-headed servers
        user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
        headers = {'User-Agent': user_agent}

        # encode the GET arguments
        data = urllib.urlencode(values)

        # make the URL into a qualified GET statement:
        get_url = url + '?' + data

        flag = 0
        attempt = 1
        while flag == 0:
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

        self.elevation = elev


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

        if not os.path.exists(OUTPUT_DIR):
            os.mkdir(OUTPUT_DIR)

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

            self.route_waypoints = {}
            self.total_miles = 0

        def add_route_waypoint(self, waypoint):
            def _extrapolate(self, waypoint1, waypoint2):
                # TODO change to calculate next valid waypoint using geometry
                """
                float dy = lat2 - lat1;
                float dx = cosf(M_PI/180*lat1)*(long2 - long1);
                float angle = atan2f(dy, dx);
                """

                lat = waypoint1.lat + 0.5 * (waypoint2.lat - waypoint1.lat)
                lon = waypoint1.lon + 0.5 * (waypoint2.lon - waypoint1.lon)
                middle_waypoint = GpsWaypoint(lat=lat, lon=lon)

                miles = haversine(waypoint1, middle_waypoint)

                if miles > MAX_WAYPOINT_MILES:
                    _extrapolate(self, waypoint1, middle_waypoint)
                    self.add_route_waypoint(middle_waypoint)
                    _extrapolate(self, middle_waypoint, waypoint2)
                else:
                    self.add_route_waypoint(middle_waypoint)

            if not self.route_waypoints:
                self.route_waypoints[0] = waypoint
            else:
                last_mileage = max(self.route_waypoints.keys())
                last_waypoint = self.route_waypoints[last_mileage]
                miles = haversine(last_waypoint, waypoint)

                if miles < MIN_WAYPOINT_MILES:
                    pass
                elif miles > MAX_WAYPOINT_MILES:
                    _extrapolate(self, last_waypoint, waypoint)
                else:
                    self.total_miles += miles
                    self.route_waypoints[self.total_miles] = waypoint

        def download_elevation(self):
            # init progress bar
            maxval = len(self.route_waypoints)
            widgets = ["Downloading %s elevation"%self.name, progressbar.Percentage(), ' ',
                       progressbar.Bar(marker='=', left='[', right=']'),
                       ' ', progressbar.ETA(), ' ', progressbar.FileTransferSpeed()]
            progress_bar = progressbar.ProgressBar(widgets=widgets, maxval=maxval)
            progress_bar.start()

            # TODO check if elevation has already been downloaded

            # download data
            i = 0
            for mileage, waypoint in self.route_waypoints.iteritems():
                waypoint.add_elevation()
                progress_bar.update(i)
                i += 1

            progress_bar.finish()
            self.write_csv()

        def write_csv(self):
            # create csv writer
            csv_path = os.path.join(OUTPUT_DIR, "%s_%s.csv" % (self.number, self.name))
            if os.path.exists(csv_path):
                os.remove(csv_path)
            fileobj = open(csv_path, "a")
            csv_writer = csv.writer(fileobj)
            csv_writer.writerow(["Latitude", "Longitude", "Name", "Elevation"])

            for mileage, waypoint in self.route_waypoints.iteritems():
                csv_writer.writerow(waypoint.get_row())
            print("wrote %s" % csv_path)

        def plot_grade(self):
            grade_data = []
            for i in range(len(self.route_waypoints)):
                wp1 = self.route_waypoints[i-1]
                wp2 = self.route_waypoints[i]

                rise = wp2.elevation - wp1.elevation
                run = haversine(wp1, wp2)

                grade_data.append(100 * rise / run)
            pdb.set_trace()

            fig, ax = plt.subplots()
            Ntotal = len(grade_data)
            N, bins, patches = ax.hist(grade_data, Ntotal)

            #I'll color code by height, but you could use any scalar

            # we need to normalize the data to 0..1 for the full
            # range of the colormap
            fracs = N.astype(float)/N.max()
            norm = colors.Normalize(fracs.min(), fracs.max())

            for thisfrac, thispatch in zip(fracs, patches):
                color = cm.jet(norm(thisfrac))
                thispatch.set_facecolor(color)

            plt.show()

    def add_route_waypoint_to_timestation(self, waypoint, timestation_index):
        # check if passed next timestation
        if ((self.timestations.get(timestation_index+1)) and
                (waypoint.lon > self.timestations.get(timestation_index+1).waypoint.lon)):
            print("grooming %s->  %s (%s)" % (
                self.timestations[timestation_index].name.ljust(32),
                self.timestations[timestation_index+1].name.ljust(32),
                waypoint))
            timestation_index += 1

        _print("%s adding to %s (%s)" % (waypoint, self.timestations.get(timestation_index).name, timestation_index))

        timestation = self.timestations.get(timestation_index)
        timestation.add_route_waypoint(waypoint)

        return timestation_index

    def process(self, elevation=False, plot=False):
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

        if elevation:
            for name, timestation in self.timestations.iteritems():
                timestation.download_elevation()
            if plot:
                for name, timestation in self.timestations.iteritems():
                    timestation.plot_grade()
        else:
            for name, timestation in self.timestations.iteritems():
                timestation.write_csv()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Wrangle RAAM GPS track to have consistent waypoint spacing.')
    parser.add_argument('-route', type=argparse.FileType('r'), dest="route", required=True,
                        help='input file, offial RAAM route.')
    parser.add_argument('-timestations', type=argparse.FileType('r'), dest="timestations", required=True,
                        help='input file, offial RAAM timestation waypoints.')
    parser.add_argument('-debug', action='store_true', default=False, dest="debug", required=False,
                        help='print debug.')
    parser.add_argument('-elev', action='store_true', default=False, dest="elevation", required=False,
                        help='download elevation data.')
    parser.add_argument('-plot', action='store_true', default=False, dest="plot", required=False,
                        help='plot % grad charts (requires -elev also set).')
    args = parser.parse_args()
    DEBUG = args.debug

    raam_track = RaamTrack(args.route, args.timestations)
    raam_track.process(elevation=args.elevation, plot=args.plot)