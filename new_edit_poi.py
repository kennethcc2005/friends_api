import boto3
import psycopg2
import ast
import numpy as np
import simplejson
import urllib
import json
import re
import os
from collections import Counter
from geopy.geocoders import Nominatim        
from boto3.session import Session

current_path= os.getcwd()
with open(current_path + '/api_key_list.config') as key_file:
    api_key_list = json.load(key_file)
api_key = api_key_list["distance_api_key_list"]
conn_str = api_key_list["conn_str"]
aws_key = api_key_list["aws_key"]
aws_secret = api_key_list["aws_secret"]
def new_poi_seasonal(data):
    '''
    CREATE TABLE seasonal_poi(
    index bigint PRIMARY KEY,
    name VARCHAR (255) NOT NULL,
    address text,
    city VARCHAR (50),
    state VARCHAR (50),
    coord_lat double precision,
    coord_long double precision,
    photo_url text,
    description text,
    season VARCHAR (25),
    link text,
    additional_info text
    );
    '''
    try:
        #read dict data and check it is in the psql or not
        desc, coord_lat, coord_long, address, city, state, link, add_info = '', None, None, None, None, None, None, ''
        season, name = data['season'], data['poi_name']
        if 'desc' in data:
            desc = data['desc']
        if 'link' in data:
            link = data['link']
        if 'city' in data:
            city = data['city']
        if 'state' in data:
            state = data['state']
        if 'additional_info' in data:
            add_info = data['additional_info']
        #Check City and State field and fill from address if needed
        if 'address' in data:
            address = data['address']
            if ('city' not in data) and (Counters(data['address'])[','] >= 2):
                add_lst = data['address'].split(',')
                state = add_lst[-1].strip()
                city = add_lst.strip() 
        #Check POI coordinates and fill from address if needed
        if ('coord_lat' not in data) or ('coord_long' not in data):
            if ('address' in data):
                geolocator = Nominatim()
                location = geolocator.geocode(data['address'])
                coord_lat, coord_long = location.latitude, location.longitude
        else:
            coord_lat, coord_long = data['coord_lat'], data['coord_long']
        #Get Photo and Save to S3 and get address
        if 'photo_src' in data:
            '''
            Update to boto3 and use from there.....
            '''
            session = Session(aws_access_key_id= aws_key,
                    aws_secret_access_key= aws_secret,
                    region_name='us-east-1')
            s3 = session.resource("s3")
            bucket_name_to_upload_image_to = 'travel-with-friends'  
            internet_image_url = data['photo_src']  
            img_ext = internet_image_url.split('.')[-1]        
            if city != None:      
                s3_image_filename = 'season_poi_images/{0}/{1}/{2}/{3}.{4}'.format(state, city, season, name, img_ext)
            else:
                s3_image_filename = 'season_poi_images/{0}/{1}/{2}.{3}'.format(state, season, name, img_ext)
            req_for_image = requests.get(internet_image_url, stream=True)
            file_object_from_req = req_for_image.raw
            req_data = file_object_from_req.read()
            # Do the actual upload to s3
            s3.Bucket(bucket_name_to_upload_image_to).put_object(Key=s3_image_filename, Body=req_data)
            print 'Done uploading image to S3 Bucket travel-with-friends'
        #Update POI if id is exisit
        conn = psycopg2.connect(conn_str)            
        cur = conn.cursor()
        if 'poi_id' in data:
            cur.execute("SELECT index,name FROM seasonal_poi WHERE index  = %s LIMIT 1;", (data['poi_id']))  
            index, name  = cur.fetchone()
            if index != None:
                cur.execute("UPDATE seasonal_poi SET (name, address, city, state, coord_lat, coord_long, photo_url, descrption, season, link, additional_info) = (%s, %s, %s, %s, %f, %f, %s, %s, %s, %s, %s) WHERE index = %s;", (name, address, city, state, coord_long, coord_lat, s3_image_filename, desc, season, link, add_info, data['poi_id']))  
                conn.commit()
        else:
            cur.execute("SELECT max(index) FROM seasonal_poi;")
            index  = cur.fetchone()[0]
            new_index = index + 1
            cur.execute("INSERT INTO seasonal_poi VALUES (%d, %s, %s, %s, %s, %f, %f, %s, %s, %s, %s, %s);", (new_index, name, address, city, state, coord_lat, coord_long, s3_image_filename, desc, season, link, add_info))
            conn.commit()
        conn.close()
        return True
    except:
        print('some errors, need to investigate: ', data)
        return False
        
