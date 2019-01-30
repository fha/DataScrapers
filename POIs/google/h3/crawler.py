import math
import numpy as np
import urllib
import json
from time import sleep

import matplotlib.pylab as plt
from h3 import h3
import folium
import haversine
import os
import glob
import re
from collections import defaultdict
import re

# This function does a nearby search on Google places API
# It takes a coordinate and the radius desired for search
# It returns a list of places with their features.
# for reference check: https://developers.google.com/places/web-service/search#PlaceSearchRequests
#
def fetchFromGooglePOI(point,radius,googlePlacesKEY):
    radiusInMeters=radius*1000;
    allDataFetched=False;
    data=[];
    url_='https://maps.googleapis.com/maps/api/place/nearbysearch/json?location='+str(point[0][0])+','+str(point[0][1])+'&radius='+str(radiusInMeters)+'&key='+googlePlacesKEY;

    i=0;
    while(not allDataFetched):
        try:
            #sending google a request
            response = urllib.request.urlopen(url_)
            #getting back data in json format
            html = response.read()
            ##cleaned=html.replace("\n","")
            json_poi=json.loads(html)
            results=json_poi['results']
            print(results)
        except:
            return [],'URL EXCEPTION';

        if len(data)==0 and len(results)!=0:
            data=results;
        elif len(results)!=0:
            data=data+results;


        #check if there are more POIs to crawl
        if 'next_page_token' in json_poi:# this means that there are more POIs to fetch, need to wait a little before sending another request
            sleep(2)
            url_='https://maps.googleapis.com/maps/api/place/nearbysearch/json?pagetoken='+str(json_poi['next_page_token'])+'&key='+str(googlePlacesKEY);
        else:
            allDataFetched=True;



    if len(data)>=50:
        status="has More POIs";
    else:
        status="crawled All POIs";
    return data,status;



#get your polygon for the area of interest here
# http://geojson.io/#map=2/20.0/0.0
geoJson ={
        "type": "Polygon",
        "coordinates":  [[
            [42.362476081807,-71.02746963500977],
            [42.37579287453795,-71.01974487304688],
            [42.384288781067205,-71.03073120117188],
            [42.3853031408436,-71.03965759277344],
            [42.383401202818526,-71.0441207885742],
            [42.38568352153437,-71.05184555053711],
            [42.38669785877541,-71.06283187866211],
            [42.38771217962709,-71.070556640625],
            [42.37427109825652,-71.08257293701172],
            [42.370086023348065,-71.08394622802734],
            [42.3614613532848,-71.07707977294922],
            [42.35765597537083,-71.08102798461914],
            [42.35359665158396,-71.09973907470703],
            [42.35245491952622,-71.10918045043945],
            [42.35524578349561,-71.11570358276367],
            [42.365266500741534,-71.1174201965332],
            [42.368817763774956,-71.11793518066406],
            [42.36907141773813,-71.12068176269531],
            [42.36932507067703,-71.12445831298828],
            [42.374017465291224,-71.1284065246582],
            [42.373383378396724,-71.13269805908203],
            [42.36843728090965,-71.13269805908203],
            [42.364885996366525,-71.13973617553711],
            [42.31590854308647,-71.1924362182617],
            [42.26511445833756,-71.17012023925781],
            [42.261557338476734,-71.09390258789062],
            [42.26867137750803,-71.04103088378906],
            [42.30676863078423,-71.03485107421875],
            [42.31819331378276,-71.02558135986328],
            [42.33722984357811,-71.00360870361328],
            [42.3476340444029,-71.01665496826172],
            [42.35423093820958,-71.02867126464842],
            [42.362476081807,-71.02746963500977]
          ]]
      }




#enter your google api key here
#googlePlacesKEY='AIzaSyBNk8TXOFpj-gyfOmot3DBiivJtppbi-lY';
#googlePlacesKEY='AIzaSyDn5N6RLoQFZLApl-Nc1kwvFFSp-gELV98'
googlePlacesKEY='AIzaSyAvUMcLfC7l838AX4IstO9ivaMhuefuVc0';

#INPUT: resolution 1 to 15 where 1 is lowest resolution and 15 is highest
resolution=9;

hexTrackFile=open('hexTrack.csv','r')
hexTracker=defaultdict(int)
hexTracker={i.split(',')[0]:int(i.split(',')[1].replace('\n','')) for i in hexTrackFile.readlines()}

#make sure you have a data folder in the same directory


#This starts crawling Google API
#This code could take a while
#to test the code you can set below QueryLimit
#This will limit the number of sent queries and finish faster

hexagons=[hexa for hexa in hexTracker];
QueryLimit=len(hexagons); #negative means query all points
data={}
inc=0
while len(hexagons)>0:
    hexa=hexagons.pop();

    #check if the hexa was crawled already:
    if os.path.isfile('data/{}.json'.format(hexa)) or hexTracker[hexa]:
        print('{} was crawled already'.format(hexa))
        hexTracker[hexa]=1;
        continue;

    #fetch the pois of this hexagon
    pointCoordinate=[tuple(h3.h3_to_geo(hexa))];
    radiusOfQuery=h3.edge_length(h3.h3_get_resolution(hexa))
    queryResults,status=fetchFromGooglePOI(pointCoordinate,radiusOfQuery,googlePlacesKEY);


    #adaptive querying if the hexagon has more POIs
    if status=='has More POIs' and h3.h3_get_resolution(hexa)<15:
            sub_hexagons=h3.h3_to_children(hexa,h3.h3_get_resolution(hexa)+1);
            hexagons=hexagons+list(sub_hexagons);
            for i in list(sub_hexagons):
                hexTracker[i]=0;
            hexTracker[hexa]=1;
            with open('data/{}.json'.format(hexa), 'w') as fp:
                json.dump({"has children":"true"}, fp)


    #save it if crawling is complete
    elif status=='crawled All POIs' or h3.h3_get_resolution(hexa)>=15:
        for place in queryResults:
            if place['place_id'] not in data:
                data[place['place_id']]=place;
        with open('data/{}.json'.format(hexa), 'w') as fp:
            json.dump(data, fp)
        hexTracker[hexa]=1;
        data={};

    #alert the user if the URL wasn't fetched because of error
    elif status=='URL EXCEPTION':
        print(status)
        hexagons=hexagons+[hexa];


    with open('hexTrack.csv','w') as trackerfile:
        for i in hexTracker:
            trackerfile.write('{},{}\n'.format(i,hexTracker[i]))
        trackerfile.close()

    print('-----------------------')
    print(status,hexa)

    #sleep(5);


    inc+=1;
    # write about the progress of the code
    if inc%10:
        print ('{} hexagons remaining to crawl'.format(len(hexagons),len(data)))
