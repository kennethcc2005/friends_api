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

def get_city_state_address(data):
    '''
    Return City, State, Address.
    If city and state not in data, get from address if possible
    '''
    city = data['city'] if 'city' in data else None
    state = data['state'] if 'state' in data else None
    if 'address' in data:
        address = data['address']
        if (city == None) and (Counters(address)[','] >= 2):
            add_lst = data['address'].split(',')
            state = add_lst[-1].strip().split(' ')[0]
            city = add_lst[-2].strip() 
    else:
        address = None
    return city, state, address

def get_coords(data):
    '''
    Return POI coord_lat, coord_long.
    If coord_lat or coord_long not in data, get from address using geolocator
    '''
    coord_lat, coord_long =  None, None
    if ('coord_lat' not in data) or ('coord_long' not in data):
        if ('address' in data):
            geolocator = Nominatim()
            location = geolocator.geocode(data['address'])
            coord_lat, coord_long = location.latitude, location.longitude
    else:
        coord_lat, coord_long = data['coord_lat'], data['coord_long']
    return coord_lat, coord_long

def upload_and_get_img_url(data):
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
    return s3_image_filename

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
        season, name = data['season'], data['poi_name']
        desc = data['desc'] if 'desc' in data else None
        link = data['link'] if 'link' in data else None
        add_info = data['additional_info'] if 'additional_info' in data else None
        #Check City and State field and fill from address if needed
        city, state, address = get_city_state_address(data)
        #Check POI coordinates and fill from address if needed
        coord_lat, coord_long = get_coords(data)
        #Get Photo and Save to S3 and get address
        s3_image_filename = upload_and_get_img_url(data) if 'photo_src' in data else None
        #Update POI if id is exisit
        conn = psycopg2.connect(conn_str)            
        cur = conn.cursor()
        if 'poi_id' in data:
            cur.execute("SELECT index,name FROM seasonal_poi WHERE index  = %s LIMIT 1;", (data['poi_id']))  
            result = cur.fetchone()
            if result != None:
                (index, name) = result
                cur.execute('''UPDATE seasonal_poi 
                                  SET (name, address, city, state, coord_lat, coord_long, photo_url, descrption, season, link,
                                      additional_info) = (%s, %s, %s, %s, %f, %f, %s, %s, %s, %s, %s) 
                                WHERE index = %d;''', 
                            (name, address, city, state, coord_long, coord_lat, s3_image_filename, desc, season, link, add_info, index))  
        else:
            cur.execute("SELECT max(index) FROM seasonal_poi;")
            result = cur.fetchone()
            if result != None:
                new_index = result[0] + 1
            else:
                new_index = 0
            cur.execute('''INSERT INTO seasonal_poi 
                           VALUES (%d, %s, %s, %s, %s, %f, %f, %s, %s, %s, %s, %s);''', 
                        (new_index, name, address, city, state, coord_lat, coord_long, s3_image_filename, desc, season, link, add_info))
        conn.commit()
        conn.close()
        return True
    except:
        print('some errors, need to investigate: ', data)
        return False
        
def udpate_poi_address(data):
    '''
    Update POI Address, return False if poi_id and poi_name not correct.
    '''
    conn = psycopg2.connect(conn_str)            
    cur = conn.cursor()
    #Check City and State field and fill from address if needed
    city, state, address = get_city_state_address(data)
    #Check POI coordinates and fill from address if needed
    coord_lat, coord_long = get_coords(data)
    if ('poi_id' not in data) and ('poi_name' not in data):
        print('Update POI Error: Needs either poi id or name to update address!')   
        conn.close()                 
        return False
    #If poi id not included and poi name has have too many results. return false
    elif ('poi_id' not in data) and ('poi_name' in data):
        name = data['poi_name']
        cur.execute('''SELECT index, name 
                         FROM poi_detail_table 
                        WHERE name = %s;''', 
                    (name))  
        name_lst = cur.fetchall()
        if len(name_lst) != 1:
            print('Update POI Error: POI name has multiple results!')  
            conn.close()                                  
            return False
        else:
            index = name_lst[0][0]
            #read dict data and check it is in the psql or not
            cur.execute('''UPDATE poi_detail_table 
                              SET (address, city, state, coord_lat, coord_long) = (%s, %s, %s, %f, %f) 
                            WHERE index = %d and name = %s;''',
                        (address, city, state, coord_lat, coord_long, index, name))  
            conn.commit()
    elif ('poi_id' in data) and ('poi_name' in data):
        index = data['poi_id']
        name = data['poi_name']
        cur.execute('''SELECT index, name 
                         FROM poi_detail_table 
                        WHERE index = %d 
                          AND name = %s;''', 
                    (index, name))  
        result = cur.fetchone()
        if result != None:
            cur.execute('''UPDATE poi_detail_table 
                              SET (address, city, state, coord_lat, coord_long) = (%s, %s, %s, %f, %f) 
                            WHERE index = %d and name = %s;''',
                        (address, city, state, coord_lat, coord_long, index, name))  
            conn.commit()
        else:
            print('Update POI Error: POI ID and name not match each other!') 
            conn.close()                       
            return False
    else:
        index = data['poi_id']
        cur.execute('''SELECT index, name 
                         FROM poi_detail_table 
                        WHERE index = %s;''', 
                    (index))  
        result = cur.fetchone()
        if result != None:
            cur.execute('''UPDATE poi_detail_table 
                              SET (address, city, state, coord_lat, coord_long) = (%s, %s, %s, %f, %f) 
                            WHERE index = %d;''',
                        (address, city, state, coord_lat, coord_long, index))  
            conn.commit()
        else:
            print('Update POI Error: POI ID not exist!')
            conn.close()            
            return False
    conn.close()
    return True
            