import helpers
import psycopg2
import os
import ast
import json
import numpy as np
from sklearn.cluster import KMeans
from geopy.geocoders import Nominatim

current_path= os.getcwd()
with open(current_path + '/api_key_list.config') as key_file:
    api_key_list = json.load(key_file)
api_key = api_key_list["distance_api_key_list"]
conn_str = api_key_list["conn_str"]

def search_query(distance):
    return 
def nightlife_city_search(address,city, state, full_trip_id):
    '''
    Get the default full trip data for each city(county)
    '''
    geolocator = Nominatim()
    location = geolocator.geocode(address)
    lat, lon = location.latitude, location.longitude
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    cur.execute('SELECT avg(num_reviews)  FROM nightlife_table WHERE ST_Distance_Sphere(geom, ST_MakePoint(%s,%s)) <= %s * 1609.34 AND rating>=3;',(lon,lat,lon,lat,5))
    good_num_reviews = cur.fetchone()[0]
    good_nightlife = []
    if good_num_reviews:
        cur.execute('SELECT *, ST_Distance_Sphere(geom, ST_MakePoint(%s,%s)) FROM nightlife_table WHERE ST_Distance_Sphere(geom, ST_MakePoint(%s,%s)) <= %s * 1609.34 AND rating>=3 AND num_reviews>=%s;',(lon,lat,lon,lat,1,good_num_reviews))
        details = cur.fetchall()
        if details:
            good_nightlife.extend(details)
        else:
            cur.execute('SELECT *, ST_Distance_Sphere(geom, ST_MakePoint(%s,%s)) FROM nightlife_table WHERE ST_Distance_Sphere(geom, ST_MakePoint(%s,%s)) <= %s * 1609.34 AND rating>=3 ORDER BY num_reviews desc limit 1;',(lon,lat,lon,lat,1))
            detail=cur.fetchone()
            if detail:
                good_nightlife.append(detail)
        if len(good_nightlife) < 7:
            cur.execute('SELECT *, ST_Distance_Sphere(geom, ST_MakePoint(%s,%s)) FROM nightlife_table WHERE ST_Distance_Sphere(geom, ST_MakePoint(%s,%s)) <= %s * 1609.34 AND rating>=3 AND num_reviews>=%s;',(lon,lat,lon,lat,1,good_num_reviews))
        details = cur.fetchall()
        if details:
            good_nightlife.extend(details)
        else:
            cur.execute('SELECT *, ST_Distance_Sphere(geom, ST_MakePoint(%s,%s)) FROM nightlife_table WHERE ST_Distance_Sphere(geom, ST_MakePoint(%s,%s)) <= %s * 1609.34 AND rating>=3 ORDER BY num_reviews desc limit 1;',(lon,lat,lon,lat,1))
            detail=cur.fetchone()
            if detail:
                good_nightlife.append(detail)


