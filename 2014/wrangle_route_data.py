import argparse
import csv
from math import radians, cos, sin, asin, sqrt
import os
import pdb


MIN_WAYPOINT_MILES = 0.25
MAX_WAYPOINT_MILES = 0.5
OUTPUT_DIR = os.path.join(os.getcwd(), "timestation_waypoints")


class GpsWaypoint(object):
    def __init__(self, lat, lon, name=None):
        self.lat = lat
        self.lon = lon
        self.name = name

    def __str__(self):
        return "%f,%f,%s\n" % (self.lat, self.lon, self.name)


def haversine(waypoint1, waypoint2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    if (type(waypoint1) == GpsWaypoint) and (type(waypoint2) == GpsWaypoint):
        # convert decimal degrees to radians
        waypoint1.lon, waypoint1.lat, waypoint2.lon, waypoint2.lat = map(radians, [waypoint1.lon, waypoint1.lat, waypoint2.lon, waypoint2.lat])
        # haversine formula
        dlon = waypoint2.lon - waypoint1.lon
        dlat = waypoint2.lat - waypoint1.lat
        a = sin(dlat/2)**2 + cos(waypoint1.lat) * cos(waypoint2.lat) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        #km = 6367 * c
        miles = 3956 * c
    else:
        miles = None

    return miles


class RaamTrack(object):
    def __init__(self, route_file, timestation_file):
        self.route_file = route_file
        self.timestation_file = timestation_file

        self.timestation_list = []

        if not os.path.exists(OUTPUT_DIR):
            os.mkdir(OUTPUT_DIR)

    class TimeStation(object):
        def __init__(self, waypoint):
            self.waypoint = waypoint
            self.full_name = waypoint.name
            self.number, self.name = self.full_name.split(":")
            self.number = self.number.strip()
            self.name = self.name.strip()

            # create csv writer
            csv_path = os.path.join(OUTPUT_DIR, "%s.csv" % self.name)
            if os.path.exists(csv_path):
                os.remove(csv_path)
            fileobj = open(csv_path, "a")
            self.csv_writer = csv.writer(fileobj)

            self.last_waypoint = None

        def extrapolate(self, waypoint1, waypoint2):
            lat = waypoint1.lat + 0.5 * (waypoint2.lat - waypoint1.lat)
            lon = waypoint1.lon + 0.5 * (waypoint2.lon - waypoint1.lon)
            middle_waypoint = GpsWaypoint(lat=lat, lon=lon)

            miles = haversine(waypoint1, middle_waypoint)
            if miles > MAX_WAYPOINT_MILES:
                self.extrapolate(waypoint1, middle_waypoint)
                self.add_waypoint(middle_waypoint)
                self.extrapolate(middle_waypoint, waypoint2)
            else:
                self.add_waypoint(middle_waypoint)

        def add_waypoint(self, waypoint):
            miles = haversine(self.last_waypoint, waypoint)

            if miles:
                if miles < MIN_WAYPOINT_MILES:
                    # too close to previous, skip
                    pass
                elif miles > MAX_WAYPOINT_MILES:
                    # too far from previous, extrapolate
                    self.extrapolate(self.last_waypoint, waypoint)
                else:
                    self.csv_writer.write(str(waypoint))
                    self.last_waypoint = waypoint

    def add_waypoint_to_timestation(self, waypoint, timestation_index):
        # check if passed next timestation
        if (len(self.timestation_list) > timestation_index+1) and \
                (waypoint.lon < self.timestation_list[timestation_index+1].waypoint.lon):
            timestation_index += 1

        timestation = self.timestation_list[timestation_index]
        timestation.add_waypoint(waypoint)

        return timestation_index

    def clean(self):
        route_reader = csv.reader(self.route_file)
        timestation_reader = csv.reader(self.timestation_file)

        for row in timestation_reader:
            if timestation_reader.line_num == 1:
                continue

            waypoint = GpsWaypoint(lat=row[0], lon=row[1], name=row[2])
            timestation = self.TimeStation(waypoint)
            self.timestation_list.append(timestation)

        timestation_index = 1
        for row in route_reader:
            if route_reader.line_num == 1:
                continue

            waypoint = GpsWaypoint(lat=float(row[0]), lon=float(row[1]), name=row[2])

            timestation_index = self.add_waypoint_to_timestation(waypoint, timestation_index)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Wrangle RAAM GPS track to have consistent waypoint spacing.')
    parser.add_argument('-route', type=argparse.FileType('r'), dest="route",
                        help='input file, offial RAAM route.')
    parser.add_argument('-timestations', type=argparse.FileType('r'), dest="timestations",
                        help='input file, offial RAAM timestation waypoints.')
    #parser.add_argument('-out_file', type=argparse.FileType('w'), dest="out_file",
    #                    default='RAAM_track_spaced.csv',
    #                    help='output file, RAAM track with constant waypoint spacing.')
    args = parser.parse_args()

    raam_track = RaamTrack(args.route, args.timestations)
    raam_track.clean()