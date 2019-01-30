import shapefile
import haversine
import numpy as np
import matplotlib.pylab as plt
import math
from collections import Counter
#from geographiclib import geodesic
from shapely.geometry import Point
from shapely.geometry import Polygon
from h3 import h3
import re
import folium
import pandas as pd
import geopy
import geopy.distance
from collections import defaultdict

def parsePoint(pointString):
    lat1, lon1 = [float(_) for _ in re.findall('[0-9.\-]+', pointString)]
    return tuple([lat1, lon1])


def calculate_initial_compass_bearing(pointA, pointB):

    if (type(pointA) != tuple) or (type(pointB) != tuple):
        raise TypeError("Only tuples are supported as arguments")

    lat1 = math.radians(pointA[0])
    lat2 = math.radians(pointB[0])

    diffLong = math.radians(pointB[1] - pointA[1])

    x = math.sin(diffLong) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1)
                                           * math.cos(lat2) * math.cos(diffLong))

    initial_bearing = math.atan2(x, y)
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360

    return compass_bearing


def convex_comb(point_a, point_b, lambda_):
    cvx_cmb = (lambda_*np.array(point_a))+((1-lambda_)*np.array(point_b))
    return cvx_cmb


def convex_comb_uniform(point_a, point_b):
    lambda_ = np.random.uniform(0.4,0.6)
    cvx_cmb = (lambda_*np.array(point_a))+((1-lambda_)*np.array(point_b))
    return cvx_cmb


def segment_length(points):
    print(points)
    return
    if len(points) == 2:
        return [haversine.haversine(points[0], points[1])]
    else:
        return [haversine.haversine(points[0], points[1])]+segment_length(points[1:])


def sample_to_points(list_):
    list_2 = []
    for i in range(0, len(list_)):
        list_2 = list_2+([i]*list_[i])
    return list_2


# the below functions are for the mapping to landuse mostly

def get_poly_in_h3hex_index(hexagons, landuseShps):
    polygonsInHexagon = {}
    for _0 in hexagons:
        for _1 in range(len(landuseShps)):
            hexPoly = Polygon([[i[0], i[1]] for i in h3.h3_to_geo_boundary(_0)])
            landusePoly = Polygon(landuseShps[_1].points)
            if landusePoly.intersects(hexPoly):
                if _0 in polygonsInHexagon:
                    polygonsInHexagon[_0] = polygonsInHexagon[_0]+[_1]
                else:
                    polygonsInHexagon[_0] = [_1]
    return polygonsInHexagon


# get the polygon for every point in a street
def get_segments_landuse(streetShps, landuseShps, landuseRcrds, polygonsInHexagon, resolution):
    streetPoints = {}
    for i in range(0, len(streetShps)):
        dummpyList = []
        for j in range(0, len(streetShps[i].points)):
            hexKey = h3.geo_to_h3(streetShps[i].points[j][0],
                                  streetShps[i].points[j][1], res=resolution)
            polyId = getPoly(hexKey, polygonsInHexagon, landuseShps, streetShps[i].points[j])
            if polyId is not None:
                dummpyList = dummpyList+[landuseRcrds[polyId][0]]
            else:
                dummpyList = dummpyList+[None]

        streetPoints[i] = dummpyList
        if i % 1000 == 1:
            print('{} street segments parsed so far'.format(i))

    print("the final length of the dict is {}".format(len(streetPoints)))
    return streetPoints


def getPoly(hexKey, polygonsInHexagon, landuseShps, point):
    if hexKey not in polygonsInHexagon:
        return -1
    for i in polygonsInHexagon[hexKey]:

        for s in range(len(landuseShps[i].parts)):
            start = landuseShps[i].parts[s]
            if s+1 < len(landuseShps[i].parts):
                end = landuseShps[i].parts[s+1]
            else:
                end = len(landuseShps[i].points)

            poly = Polygon([tuple([_[0], _[1]]) for _ in landuseShps[i].points[start:end]])
            if poly.contains(Point([point[0], point[1]])):
                return i
    return None


def plot_hexagons_in_poly(hexagons, poly):
    points_np = np.array(hexagons)
    midpoint = [np.mean(points_np[:, :, 0]), np.mean(points_np[:, :, 1])]
    bound = Polygon(poly)
    points_plotted = [i+[i[0]] for i in hexagons if bound.contains(Point(list(np.mean(i, axis=0))))]

    m = folium.Map(midpoint, tiles='stamenterrain', zoom_start=12)
    # folium.ColorLine(geoJson['coordinates']).add_to(m)
    folium.features.PolyLine(poly, color='red', weight=2).add_to(m)
    folium.features.PolyLine(points_plotted, weight=2).add_to(m)
    return m


def plotPoly(poly):
    midpoint = [np.mean([_[0] for _ in poly]), np.mean([_[1] for _ in poly])]
    m = folium.Map(midpoint, tiles='stamenterrain', zoom_start=12)
    folium.features.PolyLine(poly, color='red', weight=2).add_to(m)
    return m


def shapefile_reverse_latlon_order(x):
    j = x.points
    lis_ = []
    for _ in j:
        lis_.append((_[1], _[0]))
    x.points = lis_
    return x


def assignLanduseToHex(subHexagons, landuseShps, landuseRcrds, polygonsInHexagon, resolution):
    subHexMap = {}
    inc = 0
    for i in subHexagons:
        inc += 1
        if inc % 1000 == 0:
            print(inc)
        points = h3.h3_to_geo_boundary(i)
        parent = h3.h3_to_parent(i, resolution)
        hexagonOvlppPoly = []
        for _0 in points:
            _1 = getPoly(parent, polygonsInHexagon, landuseShps, _0)
            hexagonOvlppPoly = hexagonOvlppPoly+[_1]
        subHexMap[i] = list(set(hexagonOvlppPoly))

    subHexLanduse = {}

    for i in subHexMap:
        if len(subHexMap[i]) == 1 and subHexMap[i][0] != -1 and subHexMap[i][0] != None:
            subHexLanduse[i] = landuseRcrds[subHexMap[i][0]][0]

    return subHexLanduse, subHexMap


def getLanduse(row, hexagonsLanduse):
    hexCode = h3.geo_to_h3(row['samplePoint'][0], row['samplePoint'][1], 11)
    if hexCode in hexagonsLanduse.index:
        row['hexCode'] = hexCode
        row['landuse'] = hexagonsLanduse.loc[hexCode][0]
    else:
        row['hexCode'] = None
        row['landuse'] = None
    return row


def getStreetsInDataframe(shapefilepath,outfilepath=None,verbose=False):
    streets = shapefile.Reader(shapefilepath)
    # get the data in the right format
    streetShps = streets.shapes()
    streetShps = [shapefile_reverse_latlon_order(x) for x in streetShps]
    streetRcrds = streets.records()
    if verbose: print("read the file {} successfully".format(shapefilepath))

    if verbose: print("preparing the streets data",verbose)
    data = []
    for i in range(len(streetShps)):
        for j in range(len(streetShps[i].points)-1):
            data = data + [list([streetShps[i].points[j][0], streetShps[i].points[j][1],
                                 streetShps[i].points[j+1][0], streetShps[i].points[j+1][1],
                                 streetRcrds[i][43]])]
        if i % 1000 == 0:
            if verbose: print('{} points done'.format(i),verbose)

    dataframe = pd.DataFrame(
        data, columns=[ 'point_i_lat', 'point_i_lon', 'point_j_lat', 'point_j_lon','BSP_class'])
    if outfilepath is not None:
        dataframe.to_csv(outfilepath)
        if verbose: print("wrote the file {}".format(outfilepath))
    return dataframe;

def getSamplePointsForCrawling(streetSegments,POIs,outfile='deletethis.csv',sampleSize=100,verbose=False):
    #streetSegments = DataFrame.from_csv(infilePath)

    #if verbose: print("read the input file {} successfully".format(infilePath))
    if verbose: print("sampling points from the road network")
    # reading the street segments and preparing the data
    streetSegments = streetSegments[streetSegments['BSP_class'] != 'None']

    # add the length of the segments to the table
    streetSegments['point_i'] = streetSegments.apply(
        lambda x: tuple([x['point_i_lat'],x['point_i_lon']]), axis=1)

    streetSegments['point_j'] = streetSegments.apply(
        lambda x: tuple([x['point_j_lat'],x['point_j_lon']]), axis=1)

    # streetSegments['point_i_parsed'] = streetSegments.apply(
    #     lambda x: parsePoint(x['point_i']), axis=1)
    # streetSegments['point_j_parsed'] = streetSegments.apply(
    #     lambda x: parsePoint(x['point_j']), axis=1)

    streetSegments['length'] = streetSegments.apply(
        lambda x: haversine.haversine(x['point_i'], x['point_j']), axis=1)
    streetSegments['angle'] = streetSegments.apply(
        lambda x: calculate_initial_compass_bearing(x['point_i'], x['point_j']), axis=1)

    # sample a point on every street selected
    streetSegments['samplePoint'] = streetSegments.apply(
        lambda x: convex_comb_uniform(x['point_i'], x['point_j']), axis=1)


    #get the box
    streetSegments['box']=streetSegments.apply(
        lambda x: GetBox(x['samplePoint'], x['angle']), axis=1)

    if verbose: print("Counting nearby POIs")
    streetSegments['nearbyPoiCount']=streetSegments.apply(
        lambda x: GetPOIsCount(x['samplePoint'], x['box'],POIs), axis=1)

    streetSegments['CameraPositions'] = streetSegments.apply(
        lambda x: GetCameraPositions(x['samplePoint'], x['angle']), axis=1)

    streetSegments['considerRow']=streetSegments.apply(
        lambda x: isValidSample(x), axis=1)

    streetSegments=streetSegments[streetSegments['considerRow']==True];

    if verbose: print("Rows considered done!")
    del streetSegments['point_i']
    # del streetSegments['point_i_parsed']
    del streetSegments['point_j']
    # del streetSegments['point_j_parsed']

    if verbose: print("data was well prepared and ready for probability measurment")
    # measuring some normalization constants for a uniform probability of the segments
    landusePb = streetSegments.groupby('BSP_class').sum()
    del landusePb['angle']

    landusePb['LanduseTotalLength'] = landusePb['length']
    del landusePb['length']
    #del landusePb['nodeId']
    #del landusePb['link_id']

    landusePb = landusePb[landusePb['LanduseTotalLength'] > 5]
    landusePb['BSP_class'] = landusePb.index
    numberOfClasses = len(landusePb)

    # merging the normalizations with the street segments
    mergedSegments = pd.merge(streetSegments, landusePb, on='BSP_class')

    mergedSegments['w'] = mergedSegments['length'] / \
        (mergedSegments['LanduseTotalLength']*numberOfClasses)


    if verbose: print("data is ready to be sampled with n={} samples".format(sampleSize))
    sample = mergedSegments.sample(n=sampleSize, replace=True, weights=mergedSegments['w'],random_state=3571)
    if verbose: print("...cleaning the output")
    del sample['length']
    del sample['w']
    del sample['LanduseTotalLength']
    del sample['point_i_lat_y']
    del sample['point_i_lon_y']
    del sample['point_j_lat_y']
    del sample['point_j_lon_y']


    sample.to_csv(outfile)
    if verbose: print("wrote the file {}".format(outfile))

def GetPOIsCount(centerPoint,box,POIs):
    h3Key=h3.geo_to_h3(centerPoint[0],centerPoint[1],8)

    count=0;
    for p in POIs[h3Key]:
        if box.contains(p):
            count+=1;

    return count;

def GetBox(centerPoint,angle):

    #get the box that surrounds the sampled point "centerPoint"
    start=geopy.Point(centerPoint[0], centerPoint[1])
    d20 = geopy.distance.VincentyDistance(kilometers = 0.020)
    d50 = geopy.distance.VincentyDistance(kilometers = 0.050)
    centerEdgePoint1=d20.destination(point=centerPoint, bearing=angle)
    centerEdgePoint2=d20.destination(point=centerPoint, bearing=(angle+180)%360)
    top1=d50.destination(point=centerEdgePoint1, bearing=(angle-90)%360)
    top2=d50.destination(point=centerEdgePoint1, bearing=(angle+90)%360)
    btm1=d50.destination(point=centerEdgePoint2, bearing=(angle-90)%360)
    btm2=d50.destination(point=centerEdgePoint2, bearing=(angle+90)%360)
    box= Polygon([[top1.latitude,top1.longitude],[top2.latitude,top2.longitude],[btm1.latitude,btm1.longitude],[btm2.latitude,btm2.longitude]])

    return box;

def GetCameraPositions(centerPoint,angle):
    start=geopy.Point(centerPoint[0], centerPoint[1])
    d = geopy.distance.VincentyDistance(kilometers = 0.02)
    centerEdgePoint1=d.destination(point=centerPoint, bearing=angle)
    centerEdgePoint2=d.destination(point=centerPoint, bearing=(angle+180)%360)


    return [[centerEdgePoint1.latitude,centerEdgePoint1.longitude,(angle+180)%360],[centerEdgePoint2.latitude,centerEdgePoint2.longitude,angle]];

def getPOIsByH3Key(path,res):
    POIs=defaultdict(list)
    infile=open(path,'r')
    infile.readline()
    for line in infile.readlines():
        sp=line.split(',')
        POIs[h3.geo_to_h3(float(sp[1]),float(sp[2]),res)].append(Point([float(sp[1]),float(sp[2])]));

    return POIs;

def isValidSample(row):
    if 'commercial' in row['BSP_class'].lower():
        if row['nearbyPoiCount']>=5:
            return True;
        else:
            return False;
    elif 'residential' in row['BSP_class'].lower() or 'industrial' in row['BSP_class'].lower():
        if row['nearbyPoiCount']<1:
            return True;
        else:
            return False;
    else:
        return True;