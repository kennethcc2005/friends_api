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

def search_address_history_bool(address):
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    # cur.execute('SELECT avg(num_reviews)  FROM nightlife_table WHERE ST_Distance_Sphere(geom, ST_MakePoint(%s,%s)) <= %s * 1609.34;',(lon,lat,5))
    conn.close()
    return 
    
def nightlife_city_search(address,city, state, full_trip_id, lon=None, lat=None):
    '''
    Get the default full trip data for each city(county)
    '''
    if address != 'undefined':
        if search_address_history_bool(address):
            conn = psycopg2.connect(conn_str)
            cur = conn.cursor()
            # cur.execute('SELECT avg(num_reviews)  FROM nightlife_table WHERE ST_Distance_Sphere(geom, ST_MakePoint(%s,%s)) <= %s * 1609.34;',(lon,lat,5))
            conn.close()
            return [],[]
    if not (lon and lat):
        geolocator = Nominatim()
        location = geolocator.geocode(address)
        lat, lon = location.latitude, location.longitude
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    cur.execute('SELECT avg(num_reviews)  FROM nightlife_table WHERE ST_Distance_Sphere(geom, ST_MakePoint(%s,%s)) <= %s * 1609.34;',(lon,lat,5))
    good_num_reviews = cur.fetchone()[0]
    good_nightlife_events = []
    nightlife_ids = []
    if good_num_reviews:
        cur.execute('SELECT id, name, city, state, lat, lon, img_url, open_hours_txt, address, ST_Distance_Sphere(geom, ST_MakePoint(%s,%s))/1609.34 FROM nightlife_table WHERE ST_Distance_Sphere(geom, ST_MakePoint(%s,%s)) <= %s * 1609.34 AND rating>=3 AND num_reviews>=%s order by ST_Distance_Sphere(geom, ST_MakePoint(%s,%s)) LIMIT 7;',(lon,lat,lon,lat,5,good_num_reviews, lon,lat))
        details = cur.fetchall()
        if details:
            for nightlife_id, name, city, state, lat, lon, img_url, open_hours_txt, address, distance in details:
                good_nightlife_events.append({
                    "nightlife_id": nightlife_id,
                    "name": name,
                    "city": city,
                    "state": state,
                    "coord_lat": lat,
                    "coord_long": lon,
                    "img_url": img_url,
                    "open_hours_txt": json.loads(open_hours_txt),
                    "address": address,
                    "distance": distance
                    })
                nightlife_ids.append(nightlife_id)
            return good_nightlife_events, nightlife_ids
        else:
            return [],[]
    else:
        return [],[]
