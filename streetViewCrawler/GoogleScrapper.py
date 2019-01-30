import math
import numpy as np
import urllib
import json
from time import sleep
import matplotlib.pylab as plt
import haversine
import os
import glob
import re
from PIL import Image
import pandas as pd
import ast

def Crawl(point,angle):

    lat1,lon1=point
    APIKEY = 'AIzaSyDBRA3llQhTbqX4muyNXje3D4vEhqQa5eY'
    url_ = 'https://maps.googleapis.com/maps/api/streetview?size=640x640&source=outdoor&location=' + \
           str(lat1) + ',' + str(lon1) + '&heading=' + str(angle) + '&pitch=0&key=' + APIKEY

    response = urllib.request.urlopen(url_)
    data = response.read()
    return data;

def SimpleCrawl(row):
    cameraPositions = ast.literal_eval(row['CameraPositions'])
    point1 = [cameraPositions[0][0], cameraPositions[0][1]];
    angle1 = (cameraPositions[0][2]+180) % 360;

    try:
        idx = np.random.randint(0, 1000000)
        saveImage(Crawl(point1, angle1), point1, angle1, row, idx, 0);
        return True;
    except e:
        print('something went wrong with this one')
        return False;



def CrawlEnclosed(row):
    cameraPositions=ast.literal_eval(row['CameraPositions'])
    point1=[cameraPositions[0][0],cameraPositions[0][1]];
    angle11=(cameraPositions[0][2]+180-40)%360;
    angle12=(cameraPositions[0][2]+180+40)%360;

    point2=[cameraPositions[1][0],cameraPositions[1][1]];
    angle21 = cameraPositions[1][2]-30;
    angle22 = cameraPositions[1][2]+30;

    try:
        idx = np.random.randint(0, 1000000)
        saveImage(Crawl(point1,angle11),point1,angle11,row,idx,0);
        saveImage(Crawl(point1,angle12),point1,angle12,row,idx,1);
        #saveImage(Crawl(point2,angle21),point2,angle21,row,idx,2);
        #saveImage(Crawl(point2,angle22),point2,angle22,row,idx,3);
        print('crawled 4')
        return True;
    except e:
        print('something went wrong with this one')
        return False;

def saveImage(imageData,point,angle,row,idx,order):
    lat1,lon1=point
    try:
        if not os.path.exists('BostonStreets/{}'.format(row['BSP_class'])):
            os.makedirs('BostonStreets/{}'.format(row['BSP_class']))
        with open('BostonStreets/{}/{}_{}-{},{},{}.jpg'.format(row['BSP_class'],idx,order, lat1, lon1,angle), 'wb') as file:
            file.write(imageData)
        return True
    except e:
        print(e)
        print('failed to crawl an image')
        return False


def CrawlPoint(row):
    APIKEY = 'AIzaSyAdnhOYjYs8fy7t9-8MAaMHc1unkpZVHvg'
    lat1, lon1 = [float(_) for _ in re.findall('[0-9.\-]+', row['samplePoint'])]
    angle=row['angle'];
    for i in range(4):
        url_ = 'https://maps.googleapis.com/maps/api/streetview?size=640x640&location=' + \
                str(lat1)+','+str(lon1)+'&heading='+str(angle)+'&pitch=0&key='+APIKEY
        response = urllib.request.urlopen(url_)
        data = response.read()
        with open('BostonStreets/{}/{},{},{}.jpg'.format(row['BSP_class'],lat1,lon1,angle), 'wb') as file:
            file.write(data)
        sleep(1)
        angle+=90;

    return True

def main():

    data=pd.read_csv("sample.csv")
    data['url']=data.apply(lambda x: SimpleCrawl(x),axis=1)



main()
