#import shapefile
import haversine
import numpy as np
import matplotlib.pylab as plt
import math
from collections import Counter
from shapely.geometry import Point
from shapely.geometry import Polygon
import multiprocessing
from h3 import h3
import folium
from shapely.geometry import Polygon
from collections import Counter
import argparse
import helperFunctions as hf
import pandas as pd
import re

parser = argparse.ArgumentParser(description="sampling points/angles on streets")
parser.add_argument("-s", "--streets", type=str, required=True,
                    help="path to streets shapefile")

parser.add_argument("-o1", "--output1", type=str, default="csvStreets.csv",
                    help="path for the output file")

parser.add_argument("-o2", "--output2", type=str, default="sample.csv",
                    help="path for the output file")

parser.add_argument("-p", "--pois", type=str, required=True,
                    help="path for the POIs file")

group = parser.add_mutually_exclusive_group()
group.add_argument("-v", "--verbose", action="store_true",
                   help="toggle this if you would like to see progrss of the code")

args = parser.parse_args()





def main():
    dataframe=hf.getStreetsInDataframe(args.streets,args.output1,args.verbose);
    POIs=hf.getPOIsByH3Key(args.pois,8)
    sample=hf.getSamplePointsForCrawling(dataframe,POIs,args.output2,10,True);
    # read the shapefile
    # streets = shapefile.Reader(args.streets)
    # # get the data in the right format
    # streetShps = streets.shapes()
    # streetShps = [hf.shapefile_reverse_latlon_order(x) for x in streetShps]
    # streetRcrds = streets.records()
    # vprint("read the file {} successfully".format(args.streets))
    #
    # vprint("preparing the streets data")
    # data = []
    # for i in range(len(streetShps)):
    #     for j in range(len(streetShps[i].points)-1):
    #         data = data + [list([streetShps[i].points[j][0], streetShps[i].points[j][1],
    #                              streetShps[i].points[j+1][0], streetShps[i].points[j+1][1],
    #                              streetRcrds[i][43]])]
    #     if i % 1000 == 0:
    #         vprint('{} points done'.format(i))
    #
    # dataframe = pd.DataFrame(
    #     data, columns=[ 'point_i_lat', 'point_i_lon', 'point_j_lat', 'point_j_lon','BSP_class'])
    # dataframe.to_csv(args.output)
    # vprint("wrote the file {}".format(args.output))


if __name__ == "__main__":
    main()
